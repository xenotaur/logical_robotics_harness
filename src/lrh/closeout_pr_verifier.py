"""``closeout_pr_verifier`` -- mechanical conformance check for a `/lrh-land`
closeout PR against the plan a human approved at Step 6.

`/lrh-land` Step 7 lands closeout through a small closeout PR rather than a
direct push to `main` (a direct push is denied in this project's auto mode).
The Step 6 summary presents that closeout PR's concrete plan before it
exists, and a human's single live reply pre-authorizes its merge -- but only
when a mechanical check confirms the PR that actually appears matches the
plan (`WI-LRH-CLOSEOUT-PR-VERIFIER`, `WI-LRH-LAND-WORDING-AND-CLOSEOUT-PR`).

This module is that check. It reads state only -- diffs, a manifest of
expected fields, and reported PR state -- and never merges, pushes, edits
files, or changes any setting, mirroring the read-only, gate-owned predicate
shape of ``lrh.gate_staleness`` and ``lrh.confirm_fixes_batch``. It verifies
conformance to a plan a human has already authorized; it is not, and must
never become, an autopilot tier for the merge gate itself -- the merge gate
stays categorically excluded from any autopilot tier
(``lrh.confirm_fixes_batch``'s own module docstring makes the same point for
the confirm-fixes gate).

Three checks:

1. **Allowed paths.** Every changed path must fall under one of the allowed
   directories, or be the session index file, or be the chain-defaults
   profile (itself restricted further, below). Any other path is a
   divergence.
2. **Chain-defaults line restriction.** When the chain-defaults profile
   changed, only its ``confirmed_commit``/``confirmed_at`` assignment lines
   may differ -- any other changed line, including a comment-only or
   whitespace-only edit, is a divergence. This check compares raw text
   lines, not parsed YAML fields, because that file's blob hash (which
   binds a user's stored ``skip_if_opted_in`` consent) changes on any byte
   difference, not just a field-value change.
3. **Execution-record field conformance.** Each changed or newly-appeared
   execution record's frontmatter must match the fields the Step 6 preview
   stated for it, with one designated exception: the ``commit`` field may
   change from its pre-merge placeholder to the real merge commit -- that is
   a mechanical consequence of the merge, not a plan decision.

A separate, final check compares the caller-reported PR head SHA against the
SHA the caller states it pushed, and requires ``mergeable`` to be clean and
CI to be green -- any other combination is a divergence.
"""

from __future__ import annotations

import dataclasses
import difflib
import json as _json
import pathlib
import re
import subprocess
from collections.abc import Iterable, Mapping, Sequence

from lrh.control import parser as control_parser

_SCALAR_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):(\s|$)")

#: Path prefixes (directory families) a closeout PR may touch freely.
ALLOWED_PATH_PREFIXES: tuple[str, ...] = (
    "project/executions/",
    "project/work_items/",
    "project/workstreams/",
    "project/design/proposals/",
)

#: Exact paths (not prefixes) a closeout PR may touch freely.
ALLOWED_EXACT_PATHS: tuple[str, ...] = ("project/sessions/index.jsonl",)

#: The chain-defaults profile: allowed, but only these two fields may change.
CHAIN_DEFAULTS_PATH = "project/config/chain-defaults.yaml"
CHAIN_DEFAULTS_ALLOWED_FIELDS: tuple[str, ...] = ("confirmed_commit", "confirmed_at")

#: The one execution-record field allowed to change without being named in
#: the plan's expected fields for that record -- filling the pre-merge
#: placeholder with the real merge commit is mechanical, not a decision.
_COMMIT_FIELD = "commit"


@dataclasses.dataclass(frozen=True)
class Divergence:
    """One way the actual PR state differs from the approved plan."""

    field: str
    detail: str

    def to_mapping(self) -> dict[str, str]:
        return {"field": self.field, "detail": self.detail}


@dataclasses.dataclass(frozen=True)
class VerificationResult:
    """The outcome of verifying a closeout PR against its approved plan."""

    conforms: bool
    divergences: tuple[Divergence, ...]

    def to_mapping(self) -> dict[str, object]:
        return {
            "conforms": self.conforms,
            "divergences": [d.to_mapping() for d in self.divergences],
        }


@dataclasses.dataclass(frozen=True)
class ExecutionRecordExpectation:
    """What the Step 6 preview said a single execution record should hold.

    ``old_frontmatter`` is ``None`` when the record does not exist before
    the closeout PR (e.g. a new ``_CLOSEOUT_NOTE`` or ``_SELFREVIEW``
    record) -- the preview itself already anticipates such new records, so
    their appearance is not automatically a divergence, only a mismatch
    against ``expected_fields`` is.

    ``expected_commit`` is the *original* PR's merge commit SHA (not this
    closeout PR's own head) -- the one value the ``commit`` field is allowed
    to change to from its pre-merge placeholder. It is deliberately a
    separate field, not folded into ``expected_fields``: without it,
    accepting any new ``commit`` value whenever the plan didn't separately
    name one would let an *incorrect* commit value through undetected.
    """

    path: str
    old_frontmatter: Mapping[str, str] | None
    new_frontmatter: Mapping[str, str]
    expected_fields: Mapping[str, str]
    expected_commit: str | None = None


def classify_path(path: str) -> str:
    """Classify one changed path as ``"allowed"``, ``"chain_defaults"``, or
    ``"disallowed"``."""

    if path == CHAIN_DEFAULTS_PATH:
        return "chain_defaults"
    if path in ALLOWED_EXACT_PATHS:
        return "allowed"
    if any(path.startswith(prefix) for prefix in ALLOWED_PATH_PREFIXES):
        return "allowed"
    return "disallowed"


def check_allowed_paths(changed_paths: Iterable[str]) -> list[Divergence]:
    """Flag every changed path outside the allowed set."""

    divergences: list[Divergence] = []
    for path in changed_paths:
        if classify_path(path) == "disallowed":
            divergences.append(
                Divergence(
                    field="changed_paths",
                    detail=f"{path} is outside the allowed path set",
                )
            )
    return divergences


def _scalar_key_of(line: str) -> str | None:
    """Return the top-level YAML scalar key a line assigns, or ``None`` if
    the line isn't a bare ``key: value`` assignment (a comment, blank line,
    list item, or anything else)."""

    match = _SCALAR_KEY_RE.match(line)
    return match.group(1) if match else None


def check_chain_defaults_lines(old_text: str, new_text: str) -> list[Divergence]:
    """Flag any changed line in ``chain-defaults.yaml`` other than the two
    re-stamp fields' own assignment lines.

    This must be line-level, not field-level: the file's blob hash binds a
    user's stored ``skip_if_opted_in`` consent (`git hash-object` hashes the
    raw bytes on disk), so a comment-only or whitespace-only edit changes
    that hash and invalidates consent just as much as a real field-value
    change does -- even though both parse to the same YAML fields. Comparing
    parsed fields alone would miss exactly that case, so this compares raw
    text lines via a sequence diff instead.
    """

    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()
    matcher = difflib.SequenceMatcher(a=old_lines, b=new_lines, autojunk=False)

    divergences: list[Divergence] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        # Prefer the new-side lines (what the line reads after the change);
        # fall back to the old-side lines only for a pure deletion, which
        # has nothing on the new side to report instead.
        changed_lines = new_lines[j1:j2] if j2 > j1 else old_lines[i1:i2]
        for line in changed_lines:
            key = _scalar_key_of(line)
            if key is None or key not in CHAIN_DEFAULTS_ALLOWED_FIELDS:
                divergences.append(
                    Divergence(
                        field="chain_defaults_line",
                        detail=(
                            f"line changed and is not one of the allowed "
                            f"re-stamp fields {CHAIN_DEFAULTS_ALLOWED_FIELDS}: "
                            f"{line!r}"
                        ),
                    )
                )
    return divergences


def check_execution_record(expectation: ExecutionRecordExpectation) -> list[Divergence]:
    """Flag any frontmatter field on one execution record that isn't
    accounted for by the plan's expected fields (or the ``commit``
    placeholder-fill exception)."""

    divergences: list[Divergence] = []
    old = expectation.old_frontmatter
    new = expectation.new_frontmatter
    expected = expectation.expected_fields

    if old is None:
        # A newly-appeared record: every field it carries must be exactly
        # what the plan said this new record would hold.
        for key, value in new.items():
            if expected.get(key) != value:
                divergences.append(
                    Divergence(
                        field=f"{expectation.path}.{key}",
                        detail=(
                            f"new record field {key!r}={value!r} does not "
                            f"match the plan's expected value "
                            f"{expected.get(key)!r}"
                        ),
                    )
                )
        return divergences

    all_keys = set(old) | set(new)
    for key in sorted(all_keys):
        old_value = old.get(key)
        new_value = new.get(key)
        if old_value == new_value:
            continue
        if key == _COMMIT_FIELD and expected.get(key) is None:
            # The mechanical placeholder-fill exception -- narrow, not a
            # blanket "any new commit value is fine": it only applies when
            # the caller supplied the actual merge SHA to check against, the
            # old value was genuinely a placeholder (empty), and the new
            # value equals that exact SHA. Anything else -- no expected
            # commit supplied at all, a non-empty old value being
            # overwritten, or a new value that doesn't match -- falls
            # through to the ordinary unexpected-change check below, which
            # flags it.
            if (
                expectation.expected_commit is not None
                and not old_value
                and new_value == expectation.expected_commit
            ):
                continue
        if expected.get(key) == new_value:
            continue
        divergences.append(
            Divergence(
                field=f"{expectation.path}.{key}",
                detail=(
                    f"changed from {old_value!r} to {new_value!r}, which "
                    f"the plan did not expect (expected {expected.get(key)!r})"
                ),
            )
        )
    return divergences


def check_head_and_ci(
    *,
    actual_head: str,
    expected_head: str,
    mergeable: str,
    ci_status: str,
) -> list[Divergence]:
    """Flag a head-SHA mismatch, a non-clean mergeable state, or CI that
    isn't green."""

    divergences: list[Divergence] = []
    if actual_head != expected_head:
        divergences.append(
            Divergence(
                field="head_sha",
                detail=(
                    f"PR head {actual_head!r} does not equal the SHA the "
                    f"caller states it pushed {expected_head!r}"
                ),
            )
        )
    if mergeable != "MERGEABLE":
        divergences.append(
            Divergence(
                field="mergeable",
                detail=f"mergeable is {mergeable!r}, not MERGEABLE",
            )
        )
    if ci_status != "green":
        divergences.append(
            Divergence(
                field="ci_status", detail=f"CI status is {ci_status!r}, not green"
            )
        )
    return divergences


def verify_closeout_pr(
    *,
    changed_paths: Sequence[str],
    chain_defaults_old_text: str | None,
    chain_defaults_new_text: str | None,
    execution_records: Sequence[ExecutionRecordExpectation],
    actual_head: str,
    expected_head: str,
    mergeable: str,
    ci_status: str,
) -> VerificationResult:
    """Run every conformance check and combine the result.

    ``chain_defaults_old_text``/``chain_defaults_new_text`` are the file's
    raw text before and after the closeout commit -- raw text, not parsed
    fields, so the line-level check can see a comment or whitespace change
    the same way `git hash-object` does. Both may be ``None`` when
    ``chain-defaults.yaml`` did not change in this PR -- callers must still
    pass both or neither; passing exactly one is a caller error, not a
    divergence, and raises ``ValueError``.
    """

    if (chain_defaults_old_text is None) != (chain_defaults_new_text is None):
        raise ValueError(
            "chain_defaults_old_text and chain_defaults_new_text must "
            "both be provided, or both be None"
        )

    divergences: list[Divergence] = []
    divergences.extend(check_allowed_paths(changed_paths))

    chain_defaults_changed = CHAIN_DEFAULTS_PATH in changed_paths
    if chain_defaults_changed:
        if chain_defaults_old_text is None or chain_defaults_new_text is None:
            divergences.append(
                Divergence(
                    field=CHAIN_DEFAULTS_PATH,
                    detail=(
                        f"{CHAIN_DEFAULTS_PATH} changed but its old/new "
                        "text was not supplied for verification"
                    ),
                )
            )
        else:
            divergences.extend(
                check_chain_defaults_lines(
                    chain_defaults_old_text, chain_defaults_new_text
                )
            )

    for record in execution_records:
        divergences.extend(check_execution_record(record))

    divergences.extend(
        check_head_and_ci(
            actual_head=actual_head,
            expected_head=expected_head,
            mergeable=mergeable,
            ci_status=ci_status,
        )
    )

    return VerificationResult(conforms=not divergences, divergences=tuple(divergences))


class VerificationRunError(RuntimeError):
    """The verifier could not run at all -- distinct from a real
    divergence. Corresponds to the command's exit code 2."""


def _run(args: Sequence[str], *, cwd: pathlib.Path) -> str:
    try:
        result = subprocess.run(
            list(args),
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as err:
        raise VerificationRunError(f"failed to invoke {args[0]}: {err}") from err
    if result.returncode != 0:
        raise VerificationRunError(
            f"{' '.join(args)} failed (exit {result.returncode}): "
            f"{result.stderr.strip()}"
        )
    return result.stdout


def _show_file_at(
    project_root: pathlib.Path, commit: str, relative_path: str
) -> str | None:
    """Return file content at ``commit``, or ``None`` if the file didn't
    exist there."""

    result = subprocess.run(
        ["git", "show", f"{commit}:{relative_path}"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def _frontmatter_at(
    project_root: pathlib.Path, commit: str, relative_path: str
) -> dict[str, object] | None:
    content = _show_file_at(project_root, commit, relative_path)
    if content is None:
        return None
    try:
        return control_parser.parse_markdown_text(content).frontmatter
    except ValueError as err:
        raise VerificationRunError(
            f"could not parse frontmatter for {relative_path} at {commit}: {err}"
        ) from err


def _flat_scalar_fields(frontmatter: Mapping[str, object] | None) -> dict[str, str]:
    """Flatten a parsed frontmatter mapping's scalar top-level fields to
    strings, for the chain-defaults line-restriction comparison. Non-scalar
    values (lists, mappings) are stringified rather than dropped, so a
    genuine structural change is still caught as a divergence."""

    if frontmatter is None:
        return {}
    return {key: str(value) for key, value in frontmatter.items()}


def _classify_ci_checks(checks: Sequence[Mapping[str, object]]) -> str:
    """Classify a list of ``{"name", "state", "bucket"}`` check entries
    (``gh pr checks --json name,state,bucket`` shape) into ``"green"``,
    ``"pending"``, or ``"not_green"``.

    Pure and independently testable -- the network fetch that produces
    ``checks`` is not.
    """

    if not checks:
        return "pending"
    buckets = [str(c.get("bucket", "")).lower() for c in checks]
    if any(b in ("fail", "cancel") for b in buckets):
        return "not_green"
    if any(b in ("pending", "skipping") for b in buckets):
        return "pending"
    if all(b == "pass" for b in buckets):
        return "green"
    return "not_green"


def run_verify_pr_cli(
    *,
    pr_url: str,
    expected_head: str,
    expected_commit: str | None,
    plan_file: str,
    project_root: pathlib.Path,
) -> VerificationResult:
    """Gather live PR/git state and verify it against a plan file, then
    return the result.

    This function does the I/O the pure checks above deliberately don't --
    it is exercised by smoke/manual testing against a real checkout and
    ``gh`` auth, not by the hermetic unit suite, which targets the pure
    functions instead. It never merges, pushes, edits files, or changes any
    setting; every subprocess call here is a read.

    ``plan_file`` is a JSON file with the shape::

        {
          "execution_records": {
            "<repo-relative path>": {"<field>": "<expected value>", ...},
            ...
          }
        }

    Every execution-record path present in the PR's changed-file list but
    absent from ``execution_records`` is verified against an empty
    expectation (i.e. any changed field on it is a divergence, other than
    the ``commit`` placeholder-fill exception) -- an execution record the
    plan never mentioned is exactly the "newly appeared execution record"
    case `/lrh-land`'s own material-divergence rule already treats as
    material.

    ``expected_commit`` is the *original* PR's merge commit SHA (the value
    the closeout content's ``commit:`` placeholders are meant to be filled
    with) -- distinct from ``expected_head``, which is this closeout PR's
    own head. Pass ``None`` when no such SHA is expected yet (e.g. verifying
    before that merge has actually happened); every execution record's
    ``commit`` field is then held to the same standard as any other field,
    with no placeholder-fill exception granted.
    """

    try:
        plan_text = pathlib.Path(plan_file).expanduser().read_text(encoding="utf-8")
        plan = _json.loads(plan_text)
    except OSError as err:
        raise VerificationRunError(
            f"could not read plan file {plan_file}: {err}"
        ) from err
    except _json.JSONDecodeError as err:
        raise VerificationRunError(
            f"plan file {plan_file} is not valid JSON: {err}"
        ) from err

    expected_records: Mapping[str, Mapping[str, str]] = plan.get(
        "execution_records", {}
    )

    changed_paths_raw = _run(
        ["gh", "pr", "diff", pr_url, "--name-only"], cwd=project_root
    )
    changed_paths = [line for line in changed_paths_raw.splitlines() if line]

    pr_view_raw = _run(
        [
            "gh",
            "pr",
            "view",
            pr_url,
            "--json",
            "headRefOid,mergeable,baseRefName",
        ],
        cwd=project_root,
    )
    try:
        pr_view = _json.loads(pr_view_raw)
    except _json.JSONDecodeError as err:
        raise VerificationRunError(f"could not parse gh pr view output: {err}") from err
    actual_head = pr_view["headRefOid"]
    mergeable = pr_view["mergeable"]
    base_ref = pr_view["baseRefName"]

    merge_base = _run(
        ["git", "merge-base", f"origin/{base_ref}", actual_head], cwd=project_root
    ).strip()

    chain_defaults_old_text: str | None = None
    chain_defaults_new_text: str | None = None
    if CHAIN_DEFAULTS_PATH in changed_paths:
        chain_defaults_old_text = (
            _show_file_at(project_root, merge_base, CHAIN_DEFAULTS_PATH) or ""
        )
        chain_defaults_new_text = (
            _show_file_at(project_root, actual_head, CHAIN_DEFAULTS_PATH) or ""
        )

    execution_records: list[ExecutionRecordExpectation] = []
    for path in changed_paths:
        if classify_path(path) != "allowed" or "project/executions/" not in path:
            continue
        old_frontmatter = _frontmatter_at(project_root, merge_base, path)
        new_frontmatter = _frontmatter_at(project_root, actual_head, path)
        if new_frontmatter is None:
            # Deleted in this PR -- not a state this verifier's plan shape
            # anticipates for an execution record; treat as a divergence
            # via an explicit synthetic expectation mismatch rather than
            # silently skipping it.
            execution_records.append(
                ExecutionRecordExpectation(
                    path=path,
                    old_frontmatter=_flat_scalar_fields(old_frontmatter),
                    new_frontmatter={"__deleted__": "true"},
                    expected_fields={},
                )
            )
            continue
        execution_records.append(
            ExecutionRecordExpectation(
                path=path,
                old_frontmatter=(
                    _flat_scalar_fields(old_frontmatter)
                    if old_frontmatter is not None
                    else None
                ),
                new_frontmatter=_flat_scalar_fields(new_frontmatter),
                expected_fields=dict(expected_records.get(path, {})),
                expected_commit=expected_commit,
            )
        )

    checks_raw = _run(
        ["gh", "pr", "checks", pr_url, "--json", "name,state,bucket"],
        cwd=project_root,
    )
    try:
        checks = _json.loads(checks_raw) if checks_raw.strip() else []
    except _json.JSONDecodeError as err:
        raise VerificationRunError(
            f"could not parse gh pr checks output: {err}"
        ) from err
    ci_status = _classify_ci_checks(checks)

    return verify_closeout_pr(
        changed_paths=changed_paths,
        chain_defaults_old_text=chain_defaults_old_text,
        chain_defaults_new_text=chain_defaults_new_text,
        execution_records=execution_records,
        actual_head=actual_head,
        expected_head=expected_head,
        mergeable=mergeable,
        ci_status=ci_status,
    )


def format_text(result: VerificationResult) -> str:
    if result.conforms:
        return "conforms: yes\nno divergences"
    lines = ["conforms: no", "divergences:"]
    for d in result.divergences:
        lines.append(f"  - {d.field}: {d.detail}")
    return "\n".join(lines)


def format_json(result: VerificationResult) -> str:
    import json

    return json.dumps(result.to_mapping(), indent=2, sort_keys=True)
