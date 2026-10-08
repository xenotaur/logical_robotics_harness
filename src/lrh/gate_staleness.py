"""Semantic gate-definition staleness detection for chain-defaults consent.

Replaces the file-granular Decision 5 staleness watch (any diff to a whole
watched file invalidates stored consent) with a marker-scoped watch: only a
diff that touches lines inside a ``<!-- GATE-DEFINITION -->`` /
``<!-- /GATE-DEFINITION -->`` region invalidates consent. A change outside
any marked region (a typo fix, a comment, reordering unrelated prose) does
not.

See ``WI-LRH-CHAIN-DEFAULTS-INCREMENT-3`` and
``PROP-INVOCATION-AND-GATE-RESET`` Decision 9 for the design rationale.
"""

from __future__ import annotations

import dataclasses
import datetime
import hashlib
import json
import os
import pathlib
import re
import subprocess
import typing

_MARKER_START = "<!-- GATE-DEFINITION -->"
_MARKER_END = "<!-- /GATE-DEFINITION -->"

_HUNK_HEADER_RE = re.compile(
    r"^@@ -(?P<old_start>\d+)(?:,(?P<old_count>\d+))? "
    r"\+(?P<new_start>\d+)(?:,(?P<new_count>\d+))? @@"
)

_HARNESS_SKILLS_PREFIX = "src/lrh/skills/"

#: Gate-bearing skill files `/lrh-land` inlines, watched semantically.
#: `_shared/chain-defaults.md` is included since it is the canonical source
#: whose inlined copies (e.g. `lrh-land/references/land-workflow.md`) carry
#: the same gate-definition text.
DEFAULT_WATCHED_FILES: tuple[str, ...] = (
    "src/lrh/skills/_shared/chain-defaults.md",
    "src/lrh/skills/lrh-land/SKILL.md",
    "src/lrh/skills/lrh-land/references/land-workflow.md",
    "src/lrh/skills/lrh-execute/SKILL.md",
    "src/lrh/skills/lrh-implement/SKILL.md",
    "src/lrh/skills/lrh-confirm-fixes/SKILL.md",
    "src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md",
    "src/lrh/skills/lrh-review-response/SKILL.md",
    "src/lrh/skills/lrh-closeout/SKILL.md",
    "src/lrh/skills/lrh-closeout/references/closeout-workflow.md",
)

#: Same gate-bearing skills as `DEFAULT_WATCHED_FILES`, named relative to a
#: skills directory root (no `src/lrh/skills/` prefix) -- used to resolve
#: watch paths against an *installed* skills directory, which never has that
#: harness-repo-relative prefix.
CANONICAL_SKILL_NAMES: tuple[str, ...] = tuple(
    path[len(_HARNESS_SKILLS_PREFIX) :] for path in DEFAULT_WATCHED_FILES
)

#: `CANONICAL_SKILL_NAMES`, minus any entry whose top-level directory starts
#: with `_`. `installer.py`'s own `skill_names()` unconditionally excludes
#: such directories from every real install (see
#: `SkillSource.skill_names`), so `_shared/chain-defaults.md` never actually
#: exists at any installed target -- watching it there would make every
#: installed-target check fail closed permanently (git case) or make
#: `record_fingerprints` unable to ever complete (fingerprint case). Its
#: gate-definition text is still covered indirectly: the inlined copies that
#: *do* get installed (e.g. `lrh-land/references/land-workflow.md`) carry
#: the same text, per `DEFAULT_WATCHED_FILES`'s own docstring above.
INSTALLED_CANONICAL_SKILL_NAMES: tuple[str, ...] = tuple(
    name for name in CANONICAL_SKILL_NAMES if not name.split("/", 1)[0].startswith("_")
)

#: Where persisted content fingerprints for untracked (e.g. user-scope)
#: installed targets are stored, relative to the clone's *common* git
#: directory (`git rev-parse --git-common-dir`) -- see
#: `fingerprint_store_path`. Clone-local and shared across every worktree of
#: the same clone (the same scope as the `skip_if_opted_in` consent hash),
#: never committed: the fingerprints describe one machine's installed files.
#: Written only by `record_fingerprints` as part of a `confirmed_commit`
#: re-stamp (`lrh chain-defaults restamp`); read by `check_gate_staleness`
#: for any watch target that resolves outside `project_root`'s working tree,
#: where no git history exists to diff against `confirmed_commit`.
FINGERPRINT_STORE_RELATIVE_PATH = "lrh/chain-defaults-fingerprints.json"


class GateStalenessError(RuntimeError):
    """Raised when the staleness check itself cannot be completed."""


@dataclasses.dataclass(frozen=True)
class LineRange:
    """1-indexed, inclusive line range."""

    start: int
    end: int

    def overlaps(self, other_start: int, other_count: int) -> bool:
        if other_count <= 0:
            return False
        other_end = other_start + other_count - 1
        return self.start <= other_end and other_start <= self.end


@dataclasses.dataclass(frozen=True)
class FileStaleness:
    path: str
    stale: bool
    reason: str


@dataclasses.dataclass(frozen=True)
class WatchTarget:
    """A gate-bearing skill, resolved to where it actually lives.

    `kind` is one of:

    - ``"git"`` -- lives inside `project_root`'s working tree (either this
      harness repo's own `src/lrh/skills/` tree, or a project-local
      installed target committed to a client repo). Compared via the
      existing marker-scoped `git show` diff against `confirmed_commit`.
    - ``"fingerprint"`` -- resolved to a path outside `project_root`'s
      working tree (e.g. a user-scope install under `Path.home()`), where
      no git history exists to diff. Compared against a persisted content
      fingerprint instead.
    - ``"unresolved"`` -- the installed target itself could not be
      resolved (no `src/lrh/skills/` tree and skill-install resolution
      failed or found nothing). Always reported stale -- see
      `check_gate_staleness`'s fail-closed requirement.
    """

    canonical_name: str
    kind: typing.Literal["git", "fingerprint", "unresolved"]
    relative_path: str | None = None
    absolute_path: pathlib.Path | None = None
    strict_absence: bool = False


@dataclasses.dataclass(frozen=True)
class StalenessResult:
    confirmed_commit: str
    head: str
    stale: bool
    files: tuple[FileStaleness, ...]

    @property
    def stale_files(self) -> tuple[FileStaleness, ...]:
        return tuple(f for f in self.files if f.stale)


def extract_marker_ranges(text: str) -> tuple[LineRange, ...]:
    """Return the 1-indexed line ranges wrapped by GATE-DEFINITION markers.

    Both marker lines themselves are included in the range, so a diff hunk
    that only adds or removes a marker line still counts as touching the
    region it delimits.
    """
    lines = text.splitlines()
    ranges: list[LineRange] = []
    start_line: int | None = None
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped == _MARKER_START:
            if start_line is not None:
                raise GateStalenessError(
                    f"nested {_MARKER_START} at line {lineno} "
                    f"(unclosed marker opened at line {start_line})"
                )
            start_line = lineno
        elif stripped == _MARKER_END:
            if start_line is None:
                raise GateStalenessError(
                    f"{_MARKER_END} at line {lineno} with no matching "
                    f"{_MARKER_START}"
                )
            ranges.append(LineRange(start=start_line, end=lineno))
            start_line = None
    if start_line is not None:
        raise GateStalenessError(
            f"unclosed {_MARKER_START} opened at line {start_line}"
        )
    return tuple(ranges)


@dataclasses.dataclass(frozen=True)
class DiffHunk:
    old_start: int
    old_count: int
    new_start: int
    new_count: int


def parse_unified_diff_hunks(diff_text: str) -> tuple[DiffHunk, ...]:
    """Parse ``@@ -a,b +c,d @@`` headers from a unified diff's body.

    Accepts the abbreviated single-line form (count omitted, meaning 1),
    which real diffs emit for single-line hunks.
    """
    hunks: list[DiffHunk] = []
    for line in diff_text.splitlines():
        match = _HUNK_HEADER_RE.match(line)
        if not match:
            continue
        old_count = match.group("old_count")
        new_count = match.group("new_count")
        hunks.append(
            DiffHunk(
                old_start=int(match.group("old_start")),
                old_count=int(old_count) if old_count is not None else 1,
                new_start=int(match.group("new_start")),
                new_count=int(new_count) if new_count is not None else 1,
            )
        )
    return tuple(hunks)


def hunks_touch_marked_regions(
    hunks: tuple[DiffHunk, ...],
    old_ranges: tuple[LineRange, ...],
    new_ranges: tuple[LineRange, ...],
) -> bool:
    """True if any hunk overlaps a marked region in the old or new file."""
    for hunk in hunks:
        for old_range in old_ranges:
            if old_range.overlaps(hunk.old_start, hunk.old_count):
                return True
        for new_range in new_ranges:
            if new_range.overlaps(hunk.new_start, hunk.new_count):
                return True
    return False


def _run_git(args: list[str], project_root: pathlib.Path) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as err:
        raise GateStalenessError(f"failed to invoke git: {err}") from err
    if result.returncode not in (0, 1):
        raise GateStalenessError(
            f"git {' '.join(args)} failed (exit {result.returncode}): "
            f"{result.stderr.strip()}"
        )
    return result.stdout


def _show_file_at(
    project_root: pathlib.Path, commit: str, relative_path: str
) -> str | None:
    """Return file content at `commit`, or None if the file didn't exist.

    Assumes `commit` itself has already been validated (see
    `check_gate_staleness`'s upfront `_run_git(["rev-parse", "--verify", ...])`
    calls) -- a non-zero exit here is therefore attributed to the path, not
    the commit, and treated as "file absent at this commit" rather than
    surfaced as an error. Do not call this with an unvalidated commit-ish;
    doing so would misclassify an invalid commit the same way as a missing
    file.
    """
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


def check_file_staleness(
    project_root: pathlib.Path,
    confirmed_commit: str,
    head: str,
    relative_path: str,
    *,
    fail_closed_if_absent: bool = False,
) -> FileStaleness:
    """Check one gate-bearing file for a semantic (marker-scoped) change.

    `fail_closed_if_absent` distinguishes two different meanings of "absent
    at both commits": for the harness repo's own hardcoded self-check (the
    default), a path that was never tracked simply isn't part of this
    check -- `stale=False` is correct and must not regress. For a path
    resolved from an *installed* target (see `resolve_watch_targets`), the
    resolution already asserted this path should exist there; genuine
    absence means the check can't verify anything, so it must fail closed
    (`stale=True`) instead of silently agreeing with a no-change result.
    """
    old_content = _show_file_at(project_root, confirmed_commit, relative_path)
    new_content = _show_file_at(project_root, head, relative_path)

    if old_content is None and new_content is None:
        if fail_closed_if_absent:
            return FileStaleness(
                relative_path,
                stale=True,
                reason=(
                    "resolved installed-target path absent at both commits "
                    "-- unable to verify, failing closed"
                ),
            )
        return FileStaleness(
            relative_path, stale=False, reason="absent at both commits"
        )
    if old_content is None:
        return FileStaleness(
            relative_path, stale=True, reason="file added since confirmation"
        )
    if new_content is None:
        return FileStaleness(
            relative_path, stale=True, reason="file removed since confirmation"
        )

    diff_text = _run_git(
        ["diff", "--unified=0", confirmed_commit, head, "--", relative_path],
        project_root,
    )
    if not diff_text.strip():
        return FileStaleness(relative_path, stale=False, reason="no change")

    hunks = parse_unified_diff_hunks(diff_text)
    old_ranges = extract_marker_ranges(old_content)
    new_ranges = extract_marker_ranges(new_content)
    if hunks_touch_marked_regions(hunks, old_ranges, new_ranges):
        return FileStaleness(
            relative_path,
            stale=True,
            reason="diff touches a GATE-DEFINITION region",
        )
    return FileStaleness(
        relative_path,
        stale=False,
        reason="diff present but outside all GATE-DEFINITION regions",
    )


def resolve_watch_targets(
    project_root: pathlib.Path,
    canonical_names: tuple[str, ...] | None = None,
) -> tuple[WatchTarget, ...]:
    """Resolve each canonical gate-bearing skill to where it actually lives.

    If `project_root` has its own `src/lrh/skills/` tree, this *is* the
    harness repo (or a repo vendoring its source): watch the hardcoded
    harness-relative paths exactly as before (`DEFAULT_WATCHED_FILES`),
    unchanged, so the self-check never regresses. `canonical_names`, if
    given explicitly, must pair 1:1 with `DEFAULT_WATCHED_FILES` in this
    branch -- a length mismatch raises rather than silently truncating via
    `zip`.

    Otherwise this is a client repo with LRH installed as a package: resolve
    every *configured* installed skill target by reusing
    `lrh.skills.installer`'s own install-planning logic (a config can name
    more than one -- e.g. `targets: [claude, codex]` -- and each installed
    copy can drift independently; watching only one would let another
    configured target's material change go undetected), and watch the
    resolved paths for each -- using `INSTALLED_CANONICAL_SKILL_NAMES` by
    default (never `_`-prefixed directories, which the installer itself
    never copies) unless `canonical_names` overrides it explicitly. Each
    resolved path is classified as `"git"` (inside `project_root`'s working
    tree -- e.g. a project-local installed target committed to that repo)
    or `"fingerprint"` (outside it -- e.g. the documented default user-scope
    install under `Path.home()`, which has no git history to diff against
    at all). `canonical_name` is qualified with the target's own name (e.g.
    `"claude:lrh-land/SKILL.md"`) so two targets' fingerprints for the same
    skill name never collide in the fingerprint store or in a report.

    If the installed target(s) can't be resolved, every canonical skill
    (unqualified -- no specific target was ever determined) is returned as
    `"unresolved"` -- `check_gate_staleness`'s fail-closed requirement, not
    a caller error.
    """
    if (project_root / "src" / "lrh" / "skills").is_dir():
        names = (
            canonical_names if canonical_names is not None else CANONICAL_SKILL_NAMES
        )
        if len(names) != len(DEFAULT_WATCHED_FILES):
            raise GateStalenessError(
                f"canonical_names has {len(names)} entries but "
                f"DEFAULT_WATCHED_FILES has {len(DEFAULT_WATCHED_FILES)} -- "
                "they must pair 1:1, not be silently zip-truncated"
            )
        return tuple(
            WatchTarget(canonical_name=name, kind="git", relative_path=path)
            for name, path in zip(names, DEFAULT_WATCHED_FILES)
        )

    names = (
        canonical_names
        if canonical_names is not None
        else INSTALLED_CANONICAL_SKILL_NAMES
    )

    try:
        from lrh.skills import installer
    except ImportError:
        return tuple(
            WatchTarget(canonical_name=name, kind="unresolved") for name in names
        )

    try:
        plan = installer.resolve_agent_skills_install_plan(project_root=project_root)
        install_targets = installer.resolve_install_targets(
            target=plan.target, local=plan.local, project_root=project_root
        )
        if not install_targets:
            raise installer.SkillSourceError("no install targets resolved")
    except (installer.SkillSourceError, ValueError, IndexError, OSError):
        install_targets = None

    if install_targets is None:
        return tuple(
            WatchTarget(canonical_name=name, kind="unresolved") for name in names
        )

    resolved: list[WatchTarget] = []
    for install_target in install_targets:
        for name in names:
            qualified_name = f"{install_target.target.value}:{name}"
            absolute_path = install_target.skills_dir / name
            try:
                relative_path = absolute_path.relative_to(project_root)
            except ValueError:
                resolved.append(
                    WatchTarget(
                        canonical_name=qualified_name,
                        kind="fingerprint",
                        absolute_path=absolute_path,
                    )
                )
            else:
                resolved.append(
                    WatchTarget(
                        canonical_name=qualified_name,
                        kind="git",
                        relative_path=str(relative_path),
                        strict_absence=True,
                    )
                )
    return tuple(resolved)


def compute_fingerprint(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def canonical_confirmed_at(value: object) -> str:
    """Normalize a `confirmed_at` value to its one canonical comparison form.

    The canonical form is ISO-8601 UTC at second precision with a trailing
    ``Z`` (e.g. ``2026-09-22T03:50:48Z``). The same instant reaches this
    module in different shapes: `yaml.safe_load` turns an unquoted timestamp
    into a timezone-aware `datetime` (whose `str()` is
    ``2026-09-22 03:50:48+00:00``), while the shell snippet in
    `_shared/chain-defaults.md` passes the raw profile text. Every comparison
    goes through this function so both paths agree.

    Raises `GateStalenessError` -- callers treat that as fail-closed -- for
    anything that is not an unambiguous instant at second precision: an
    unparseable string, a timezone-less value (its instant is undefined),
    or a value carrying fractional seconds (truncating it could make two
    distinct stamps compare equal).
    """
    if isinstance(value, datetime.datetime):
        parsed = value
    elif isinstance(value, str):
        text = value.strip()
        if text.endswith("Z") or text.endswith("z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.datetime.fromisoformat(text)
        except ValueError as err:
            raise GateStalenessError(
                f"confirmed_at {value!r} is not an ISO-8601 timestamp"
            ) from err
    else:
        raise GateStalenessError(
            f"confirmed_at {value!r} is not a timestamp (got "
            f"{type(value).__name__})"
        )
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise GateStalenessError(
            f"confirmed_at {value!r} has no timezone -- its instant is undefined"
        )
    if parsed.microsecond:
        raise GateStalenessError(
            f"confirmed_at {value!r} has fractional seconds -- the canonical "
            "form is second precision"
        )
    utc = parsed.astimezone(datetime.timezone.utc)
    return utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def fingerprint_store_path(project_root: pathlib.Path) -> pathlib.Path:
    """Return the fingerprint store's path in the clone's common git dir.

    `git rev-parse --git-common-dir` may print a path relative to
    `project_root` (e.g. ``.git``); resolve it explicitly rather than
    joining blindly, since `pathlib`'s ``/`` discards its left operand when
    the right one is already absolute. Raises `GateStalenessError` when the
    git directory cannot be resolved.
    """
    common_dir = _run_git(["rev-parse", "--git-common-dir"], project_root).strip()
    if not common_dir:
        raise GateStalenessError(
            f"could not resolve the git common dir for {project_root}"
        )
    common_path = pathlib.Path(common_dir)
    if not common_path.is_absolute():
        common_path = project_root / common_path
    return common_path.resolve() / FINGERPRINT_STORE_RELATIVE_PATH


@dataclasses.dataclass(frozen=True)
class FingerprintStore:
    """The persisted fingerprint store, bound to the stamp it was written for.

    `confirmed_commit` is the full resolved SHA and `confirmed_at` is in
    `canonical_confirmed_at` form. `check_gate_staleness` accepts the store
    only when both equal the stamp of the profile it is checking, so a store
    written without a matching committed profile (a failed profile write, a
    declined `main` push, or a branch still carrying an older profile) can
    never make an untracked target read fresh.
    """

    confirmed_commit: str
    confirmed_at: str
    fingerprints: dict[str, str]


def load_fingerprint_store(project_root: pathlib.Path) -> FingerprintStore | None:
    """Load the persisted fingerprint store, or None if unavailable.

    Returns None (never raises) on a missing, unreadable, or malformed store
    -- including one missing either stamp key, such as the old bare
    name-to-hash map -- and when the git common dir cannot be resolved.
    `check_gate_staleness` treats None as "no fingerprint on record" and
    fails every untracked target closed.
    """
    try:
        path = fingerprint_store_path(project_root)
    except GateStalenessError:
        return None
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    commit = data.get("confirmed_commit")
    confirmed_at = data.get("confirmed_at")
    fingerprints = data.get("fingerprints")
    if not isinstance(commit, str) or not commit:
        return None
    if not isinstance(confirmed_at, str) or not confirmed_at:
        return None
    if not isinstance(fingerprints, dict):
        return None
    return FingerprintStore(
        confirmed_commit=commit,
        confirmed_at=confirmed_at,
        fingerprints={str(key): str(value) for key, value in fingerprints.items()},
    )


@dataclasses.dataclass(frozen=True)
class FingerprintPlanEntry:
    name: str
    #: The installed file, or None for a `removed` entry.
    absolute_path: pathlib.Path | None
    #: The new hash, or None for a `removed` entry.
    fingerprint: str | None
    #: One of ``"new"``, ``"unchanged"``, ``"changed"``, ``"removed"``.
    comparison: str


@dataclasses.dataclass(frozen=True)
class FingerprintPlan:
    entries: tuple[FingerprintPlanEntry, ...]
    #: The complete map a write would persist (whole-map replacement).
    fingerprints: dict[str, str]
    #: True when nothing needs writing: no fingerprint-kind targets and no
    #: stored entries to remove.
    nothing_to_do: bool


def plan_fingerprints(
    targets: tuple[WatchTarget, ...],
    stored: dict[str, str] | None,
) -> FingerprintPlan:
    """Compute what recording fingerprints would write, without writing.

    Both `--dry-run` and the real write use this, so the preview and the
    write cannot diverge. Every target is checked before anything is
    computed into the plan: raises `GateStalenessError` if **any** target is
    `"unresolved"` or any fingerprint-kind target file is missing -- a
    re-stamp must never record an empty or partial fingerprint set.
    """
    for target in targets:
        if target.kind == "unresolved":
            raise GateStalenessError(
                "cannot record fingerprints: installed target "
                f"{target.canonical_name} could not be resolved"
            )
        if target.kind == "fingerprint" and (
            target.absolute_path is None or not target.absolute_path.is_file()
        ):
            raise GateStalenessError(
                f"cannot fingerprint missing installed target: "
                f"{target.canonical_name} ({target.absolute_path})"
            )
    stored = stored or {}
    entries: list[FingerprintPlanEntry] = []
    fingerprints: dict[str, str] = {}
    for target in targets:
        if target.kind != "fingerprint":
            continue
        assert target.absolute_path is not None  # checked above
        try:
            content = target.absolute_path.read_bytes()
        except OSError as err:
            raise GateStalenessError(
                f"cannot read installed target {target.canonical_name} "
                f"({target.absolute_path}): {err}"
            ) from err
        value = compute_fingerprint(content)
        fingerprints[target.canonical_name] = value
        previous = stored.get(target.canonical_name)
        if previous is None:
            comparison = "new"
        elif previous == value:
            comparison = "unchanged"
        else:
            comparison = "changed"
        entries.append(
            FingerprintPlanEntry(
                name=target.canonical_name,
                absolute_path=target.absolute_path,
                fingerprint=value,
                comparison=comparison,
            )
        )
    for name in sorted(set(stored) - set(fingerprints)):
        entries.append(
            FingerprintPlanEntry(
                name=name, absolute_path=None, fingerprint=None, comparison="removed"
            )
        )
    return FingerprintPlan(
        entries=tuple(entries),
        fingerprints=fingerprints,
        nothing_to_do=not fingerprints and not stored,
    )


def write_fingerprint_store(
    project_root: pathlib.Path, store: FingerprintStore
) -> None:
    """Atomically persist `store` to the clone's common git dir."""
    path = fingerprint_store_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(
            {
                "confirmed_commit": store.confirmed_commit,
                "confirmed_at": store.confirmed_at,
                "fingerprints": store.fingerprints,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    # Atomic write: a temp file in the same directory (so the rename is on
    # the same filesystem), then os.replace -- a process interrupted
    # mid-write must never leave a partial/corrupt store behind, since
    # `load_fingerprint_store` treats any unreadable store as "no
    # fingerprint on record" and fails every untracked target closed.
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(payload, encoding="utf-8")
    os.replace(tmp_path, path)


def record_fingerprints(
    project_root: pathlib.Path,
    targets: tuple[WatchTarget, ...],
    confirmed_commit: str,
    confirmed_at: str,
) -> FingerprintPlan:
    """Compute and persist current-content fingerprints for untracked targets.

    Runs only as part of a `confirmed_commit` re-stamp (`lrh chain-defaults
    restamp`), never on its own: the store is bound to the same
    `(confirmed_commit, confirmed_at)` stamp the profile is being re-stamped
    to, so git-tracked and fingerprinted targets share one confirmation
    baseline. `confirmed_commit` must be a full SHA and `confirmed_at` is
    normalized via `canonical_confirmed_at`.

    Raises (writing nothing) on any unresolved target or missing installed
    file -- see `plan_fingerprints`. Replaces the whole map: entries for
    targets no longer configured are dropped. When there is nothing to do
    (no fingerprint-kind targets and no stored entries) nothing is written;
    when stored entries exist but no fingerprint-kind targets remain, an
    empty map is written so the `removed` entries actually go away.
    """
    existing = load_fingerprint_store(project_root)
    plan = plan_fingerprints(targets, existing.fingerprints if existing else None)
    if plan.nothing_to_do:
        return plan
    write_fingerprint_store(
        project_root,
        FingerprintStore(
            confirmed_commit=confirmed_commit,
            confirmed_at=canonical_confirmed_at(confirmed_at),
            fingerprints=plan.fingerprints,
        ),
    )
    return plan


def _store_mismatch_reason(
    store: FingerprintStore,
    resolved_commit: str,
    confirmed_at: object | None,
) -> str | None:
    """Return why `store` can't be trusted for this stamp, or None if it can."""
    if confirmed_at is None:
        return (
            "no confirmed_at supplied, so the fingerprint store's stamp cannot "
            "be validated -- failing closed"
        )
    try:
        wanted_at = canonical_confirmed_at(confirmed_at)
        stored_at = canonical_confirmed_at(store.confirmed_at)
    except GateStalenessError as err:
        return f"{err} -- failing closed"
    if store.confirmed_commit != resolved_commit or stored_at != wanted_at:
        return (
            "fingerprint store was recorded for a different confirmation "
            "stamp -- failing closed"
        )
    return None


def check_target_staleness(
    project_root: pathlib.Path,
    confirmed_commit: str,
    head: str,
    target: WatchTarget,
    fingerprints: dict[str, str] | None,
    store_unavailable_reason: str | None = None,
) -> FileStaleness:
    """Check one resolved `WatchTarget` for staleness, by whichever means
    its `kind` supports.

    `store_unavailable_reason`, when set, fails every fingerprint-kind
    target closed with that reason (e.g. the store's stamp does not match
    the profile being checked).
    """
    if target.kind == "unresolved":
        return FileStaleness(
            target.canonical_name,
            stale=True,
            reason="installed target could not be resolved -- failing closed",
        )
    if target.kind == "git":
        if target.relative_path is None:
            raise GateStalenessError(
                f"WatchTarget {target.canonical_name!r} has kind='git' but "
                "no relative_path -- malformed WatchTarget"
            )
        return check_file_staleness(
            project_root,
            confirmed_commit,
            head,
            target.relative_path,
            fail_closed_if_absent=target.strict_absence,
        )
    # kind == "fingerprint"
    if target.absolute_path is None:
        raise GateStalenessError(
            f"WatchTarget {target.canonical_name!r} has kind='fingerprint' "
            "but no absolute_path -- malformed WatchTarget"
        )
    if store_unavailable_reason is not None:
        return FileStaleness(
            target.canonical_name, stale=True, reason=store_unavailable_reason
        )
    if fingerprints is None or target.canonical_name not in fingerprints:
        return FileStaleness(
            target.canonical_name,
            stale=True,
            reason=(
                "no persisted content fingerprint on record for this "
                "untracked installed target -- failing closed"
            ),
        )
    if not target.absolute_path.is_file():
        return FileStaleness(
            target.canonical_name,
            stale=True,
            reason="installed target file missing -- failing closed",
        )
    try:
        content = target.absolute_path.read_bytes()
    except OSError:
        return FileStaleness(
            target.canonical_name,
            stale=True,
            reason="installed target file unreadable -- failing closed",
        )
    current = compute_fingerprint(content)
    stored = fingerprints[target.canonical_name]
    if current != stored:
        return FileStaleness(
            target.canonical_name,
            stale=True,
            reason="installed file content differs from persisted fingerprint",
        )
    return FileStaleness(
        target.canonical_name,
        stale=False,
        reason="installed file content matches persisted fingerprint",
    )


def check_gate_staleness(
    project_root: pathlib.Path,
    confirmed_commit: str,
    head: str = "HEAD",
    watched_files: tuple[str, ...] | None = None,
    confirmed_at: object | None = None,
) -> StalenessResult:
    """Check every watched gate-bearing file for semantic staleness.

    `watched_files`, when given explicitly, is checked exactly as before --
    a fixed tuple of paths relative to `project_root`, compared via git
    history only (the harness repo's own self-check, and any caller that
    already knows its watch paths are git-tracked within `project_root`).

    When omitted (the default), the watch set is resolved dynamically via
    `resolve_watch_targets`, which is target-aware: it watches this
    harness repo's own paths when present, or the actually-installed skill
    target's paths otherwise -- via git history when that target lives
    inside `project_root`'s working tree, or via a persisted content
    fingerprint when it doesn't.

    `confirmed_at` is the profile's own `confirmed_at` (a `datetime` from a
    YAML load, or the raw text from the shell snippet). The fingerprint
    store is accepted only when its stamp equals `(confirmed_commit resolved
    to a full SHA, canonical confirmed_at)`; without `confirmed_at`, every
    fingerprint-kind target fails closed. Git-tracked targets don't use it.
    """
    if not confirmed_commit or confirmed_commit == "null":
        raise GateStalenessError(
            "confirmed_commit is null/empty -- no prior confirmation on "
            "record; the first-encounter propose-and-confirm path applies "
            "instead, not this staleness check"
        )
    # Validate confirmed_commit up front, before any per-file _show_file_at
    # call: an invalid/unresolvable commit must surface as an error, not be
    # silently misread as "every watched file was added since confirmation"
    # (which is what a bare _show_file_at failure on a bad commit would
    # otherwise look like).
    resolved_commit = _run_git(
        ["rev-parse", "--verify", f"{confirmed_commit}^{{commit}}"], project_root
    ).strip()
    resolved_head = _run_git(["rev-parse", head], project_root).strip()

    if watched_files is not None:
        files = tuple(
            check_file_staleness(project_root, confirmed_commit, resolved_head, path)
            for path in watched_files
        )
    else:
        targets = resolve_watch_targets(project_root)
        fingerprints: dict[str, str] | None = None
        store_reason: str | None = None
        if any(target.kind == "fingerprint" for target in targets):
            store = load_fingerprint_store(project_root)
            if store is not None:
                store_reason = _store_mismatch_reason(
                    store, resolved_commit, confirmed_at
                )
                fingerprints = store.fingerprints
        files = tuple(
            check_target_staleness(
                project_root,
                confirmed_commit,
                resolved_head,
                target,
                fingerprints,
                store_reason,
            )
            for target in targets
        )

    return StalenessResult(
        confirmed_commit=confirmed_commit,
        head=resolved_head,
        stale=any(f.stale for f in files),
        files=files,
    )


def format_json(result: StalenessResult) -> str:
    return json.dumps(
        {
            "confirmed_commit": result.confirmed_commit,
            "head": result.head,
            "stale": result.stale,
            "files": [
                {"path": f.path, "stale": f.stale, "reason": f.reason}
                for f in result.files
            ],
        },
        indent=2,
    )


def format_text(result: StalenessResult) -> str:
    lines = [
        f"confirmed_commit: {result.confirmed_commit}",
        f"head: {result.head}",
        f"stale: {result.stale}",
    ]
    if result.stale:
        lines.append("stale files:")
        for stale_file in result.stale_files:
            lines.append(f"  - {stale_file.path}: {stale_file.reason}")
    else:
        lines.append("no gate-definition changes since confirmation")
    return "\n".join(lines)
