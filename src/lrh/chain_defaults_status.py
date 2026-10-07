"""Single-read status view over `project/config/chain-defaults.yaml`.

Backs `lrh chain-defaults status` / the `/lrh-config-gates` skill: reads the
profile file, the local git-config skip-consent hash, and the
`gate_staleness` staleness result together, in one structured call, instead
of the several separate manual reads (`git config --get`, `git hash-object`,
`lrh chain-defaults check-staleness`, reading the raw YAML) this session's
own `WI-SKILLS-LRH-CONFIG-GATES` was filed to replace.

Only the 4 fields `chain-defaults.md` documents as human-decidable are
reported as configurable; `closeout_with_merge` is reported read-only, per
`chain-defaults.md:40-46` -- it is the shipped, unconditional `/lrh-land`
merge+closeout behavior, not a toggle any gate branches on.
"""

from __future__ import annotations

import dataclasses
import datetime
import json
import os
import pathlib
import re
import subprocess

import yaml

from lrh import gate_staleness

#: Path to the chain-defaults profile, relative to the project root.
CHAIN_DEFAULTS_PATH = "project/config/chain-defaults.yaml"

#: The git-config key `skip_if_opted_in` consent is stored under.
CONSENT_HASH_CONFIG_KEY = "lrh.chainDefaults.skipConsentHash"

#: The 4 fields `chain-defaults.md` documents as human-decidable.
HUMAN_DECIDABLE_FIELDS = (
    "chain_init_confirmation",
    "confirm_fixes_batch",
    "completion_condition",
    "stop_work_condition",
)

#: Documented read-only per `chain-defaults.md:40-46` -- the shipped,
#: unconditional `/lrh-land` merge+closeout behavior, never a toggle.
READ_ONLY_FIELD = "closeout_with_merge"


class ChainDefaultsStatusError(RuntimeError):
    """Raised when the status read itself cannot be completed."""


@dataclasses.dataclass(frozen=True)
class ConsentStatus:
    #: The hash currently recorded in local git config, or None if unset.
    stored_hash: str | None
    #: The current blob hash of the on-disk chain-defaults.yaml.
    current_hash: str
    #: True iff stored_hash is set and matches current_hash exactly.
    valid: bool


@dataclasses.dataclass(frozen=True)
class ChainDefaultsStatus:
    profile_exists: bool
    fields: dict[str, object]
    read_only_fields: dict[str, object]
    consent: ConsentStatus
    #: None when confirmed_commit is null/absent -- first-encounter case,
    #: no staleness check applies yet.
    staleness: gate_staleness.StalenessResult | None
    staleness_error: str | None


def _run_git(
    args: list[str], project_root: pathlib.Path
) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as err:
        raise ChainDefaultsStatusError(f"failed to invoke git: {err}") from err


def read_consent_hash(project_root: pathlib.Path) -> str | None:
    """Read the locally stored skip-consent hash, or None if unset.

    Deliberately `--local`, not `--worktree`: per this session's own
    empirical verification, `git config --local` is shared across every
    worktree of the *same* clone (the common `.git/config`) but never
    shared across independent clones -- see the module docstring and
    `chain-defaults.md`'s per-clone scope note.
    """
    result = _run_git(
        ["config", "--local", "--get", CONSENT_HASH_CONFIG_KEY], project_root
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def hash_object(project_root: pathlib.Path, relative_path: str) -> str:
    """Return the git blob hash of the file's current on-disk content.

    `git hash-object` hashes whatever is on disk regardless of whether the
    path is tracked -- this does not require the file to already be tracked
    by git.
    """
    result = _run_git(["hash-object", relative_path], project_root)
    if result.returncode != 0:
        raise ChainDefaultsStatusError(
            f"git hash-object {relative_path} failed: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def load_profile(project_root: pathlib.Path) -> dict | None:
    """Load and parse chain-defaults.yaml, or None if it does not exist."""
    path = project_root / CHAIN_DEFAULTS_PATH
    if not path.exists():
        return None
    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError as err:
        raise ChainDefaultsStatusError(
            f"{CHAIN_DEFAULTS_PATH} is not valid YAML: {err}"
        ) from err
    if not isinstance(data, dict):
        raise ChainDefaultsStatusError(
            f"{CHAIN_DEFAULTS_PATH} did not parse to a mapping"
        )
    return data


def compute_status(
    project_root: pathlib.Path,
    head: str = "HEAD",
) -> ChainDefaultsStatus:
    """Compute the full status view in one read.

    Fails safe on every unknown-shape input -- a missing file, a missing
    field, or a missing `confirmed_commit` is reported as an absent/None
    value in the result, never raised, so a caller (e.g. the
    `/lrh-config-gates` skill) can present "not yet configured" state
    instead of crashing. Only a git invocation failure or malformed YAML
    raises `ChainDefaultsStatusError`.
    """
    profile = load_profile(project_root)
    profile_exists = profile is not None
    profile = profile or {}

    fields = {name: profile.get(name) for name in HUMAN_DECIDABLE_FIELDS}
    read_only_fields = {READ_ONLY_FIELD: profile.get(READ_ONLY_FIELD)}

    current_hash = (
        hash_object(project_root, CHAIN_DEFAULTS_PATH) if profile_exists else ""
    )
    stored_hash = read_consent_hash(project_root)
    consent = ConsentStatus(
        stored_hash=stored_hash,
        current_hash=current_hash,
        valid=bool(
            profile_exists and stored_hash is not None and stored_hash == current_hash
        ),
    )

    confirmed_commit = profile.get("confirmed_commit")
    staleness: gate_staleness.StalenessResult | None = None
    staleness_error: str | None = None
    if confirmed_commit:
        try:
            staleness = gate_staleness.check_gate_staleness(
                project_root=project_root,
                confirmed_commit=confirmed_commit,
                head=head,
                confirmed_at=profile.get("confirmed_at"),
            )
        except gate_staleness.GateStalenessError as err:
            staleness_error = str(err)
    else:
        staleness_error = (
            "confirmed_commit is null/absent -- no prior confirmation on record"
        )

    return ChainDefaultsStatus(
        profile_exists=profile_exists,
        fields=fields,
        read_only_fields=read_only_fields,
        consent=consent,
        staleness=staleness,
        staleness_error=staleness_error,
    )


def format_json(status: ChainDefaultsStatus) -> str:
    return json.dumps(
        {
            "profile_exists": status.profile_exists,
            "fields": status.fields,
            "read_only_fields": status.read_only_fields,
            "consent": {
                "stored_hash": status.consent.stored_hash,
                "current_hash": status.consent.current_hash,
                "valid": status.consent.valid,
            },
            "staleness": (
                {
                    "confirmed_commit": status.staleness.confirmed_commit,
                    "head": status.staleness.head,
                    "stale": status.staleness.stale,
                    "files": [
                        {"path": f.path, "stale": f.stale, "reason": f.reason}
                        for f in status.staleness.files
                    ],
                }
                if status.staleness is not None
                else None
            ),
            "staleness_error": status.staleness_error,
        },
        indent=2,
    )


def format_text(status: ChainDefaultsStatus) -> str:
    lines: list[str] = []
    if not status.profile_exists:
        lines.append(f"{CHAIN_DEFAULTS_PATH}: does not exist")
        return "\n".join(lines)

    lines.append("Human-decidable fields:")
    for name in HUMAN_DECIDABLE_FIELDS:
        lines.append(f"  {name}: {status.fields[name]!r}")
    lines.append("Read-only fields (not a user-facing toggle):")
    lines.append(f"  {READ_ONLY_FIELD}: {status.read_only_fields[READ_ONLY_FIELD]!r}")

    lines.append("Consent (skip_if_opted_in, per-clone scope):")
    lines.append(f"  stored_hash: {status.consent.stored_hash}")
    lines.append(f"  current_hash: {status.consent.current_hash}")
    lines.append(f"  valid: {status.consent.valid}")

    lines.append("Staleness:")
    if status.staleness is not None:
        lines.append(f"  stale: {status.staleness.stale}")
        if status.staleness.stale:
            for stale_file in status.staleness.stale_files:
                lines.append(f"    - {stale_file.path}: {stale_file.reason}")
    else:
        lines.append(f"  unavailable: {status.staleness_error}")

    return "\n".join(lines)


@dataclasses.dataclass(frozen=True)
class RestampPlan:
    """Everything `lrh chain-defaults restamp` would write, computed up front.

    `--dry-run` prints this; the real run writes exactly this, so the
    preview and the write cannot diverge.
    """

    #: The profile's `confirmed_commit` before the re-stamp, or None.
    previous_confirmed_commit: str | None
    #: The staleness result being cleared (the stale-files payload the
    #: human must have been shown), or None with `staleness_error` set.
    staleness: gate_staleness.StalenessResult | None
    staleness_error: str | None
    fingerprint_plan: gate_staleness.FingerprintPlan
    #: Full SHA of HEAD, written to both the profile and the store.
    new_confirmed_commit: str
    #: Canonical `confirmed_at`, written to both the profile and the store.
    new_confirmed_at: str


def plan_restamp(
    project_root: pathlib.Path,
    head: str = "HEAD",
    now: datetime.datetime | None = None,
) -> RestampPlan:
    """Compute a re-stamp of `confirmed_commit`/`confirmed_at` plus the
    fingerprint store bound to that same stamp, without writing anything.

    Requires the profile file to exist -- the first-encounter "file absent"
    path writes the file first, then re-stamps. Raises
    `ChainDefaultsStatusError` when any watch target is unresolved or any
    installed target file is missing, so a refused re-stamp writes nothing.
    """
    profile = load_profile(project_root)
    if profile is None:
        raise ChainDefaultsStatusError(
            f"{CHAIN_DEFAULTS_PATH} does not exist -- write the profile first, "
            "then re-stamp"
        )
    previous = profile.get("confirmed_commit")
    previous_commit = str(previous) if previous else None

    staleness: gate_staleness.StalenessResult | None = None
    staleness_error: str | None = None
    if previous_commit and previous_commit != "null":
        try:
            staleness = gate_staleness.check_gate_staleness(
                project_root=project_root,
                confirmed_commit=previous_commit,
                head=head,
                confirmed_at=profile.get("confirmed_at"),
            )
        except gate_staleness.GateStalenessError as err:
            staleness_error = str(err)
    else:
        staleness_error = (
            "confirmed_commit is null/absent -- no prior confirmation on record"
        )

    try:
        targets = gate_staleness.resolve_watch_targets(project_root)
        existing = gate_staleness.load_fingerprint_store(project_root)
        fingerprint_plan = gate_staleness.plan_fingerprints(
            targets, existing.fingerprints if existing else None
        )
    except gate_staleness.GateStalenessError as err:
        raise ChainDefaultsStatusError(f"refusing to re-stamp: {err}") from err

    result = _run_git(["rev-parse", "--verify", f"{head}^{{commit}}"], project_root)
    if result.returncode != 0:
        raise ChainDefaultsStatusError(
            f"could not resolve {head}: {result.stderr.strip()}"
        )
    moment = now or datetime.datetime.now(datetime.timezone.utc)
    try:
        new_at = gate_staleness.canonical_confirmed_at(moment.replace(microsecond=0))
    except gate_staleness.GateStalenessError as err:
        raise ChainDefaultsStatusError(str(err)) from err

    return RestampPlan(
        previous_confirmed_commit=previous_commit,
        staleness=staleness,
        staleness_error=staleness_error,
        fingerprint_plan=fingerprint_plan,
        new_confirmed_commit=result.stdout.strip(),
        new_confirmed_at=new_at,
    )


_CONFIRMED_COMMIT_LINE = re.compile(r"^confirmed_commit:.*$", re.MULTILINE)
_CONFIRMED_AT_LINE = re.compile(r"^confirmed_at:.*$", re.MULTILINE)


def _restamped_profile_text(text: str, commit: str, confirmed_at: str) -> str:
    """Rewrite only the two stamp lines, leaving every other byte unchanged."""
    for pattern, key in (
        (_CONFIRMED_COMMIT_LINE, "confirmed_commit"),
        (_CONFIRMED_AT_LINE, "confirmed_at"),
    ):
        count = len(pattern.findall(text))
        if count != 1:
            raise ChainDefaultsStatusError(
                f"{CHAIN_DEFAULTS_PATH} must have exactly one top-level "
                f"`{key}:` line to re-stamp (found {count})"
            )
    text = _CONFIRMED_COMMIT_LINE.sub(f"confirmed_commit: {commit}", text)
    return _CONFIRMED_AT_LINE.sub(f"confirmed_at: {confirmed_at}", text)


def apply_restamp(project_root: pathlib.Path, plan: RestampPlan) -> None:
    """Write the fingerprint store, then the profile's two stamp lines.

    Store first, profile second, both bound to the same stamp. If the
    profile write fails (or the re-stamp is never committed), the store's
    stamp matches no profile and `check_gate_staleness` fails every
    fingerprint-kind target closed.
    """
    path = project_root / CHAIN_DEFAULTS_PATH
    try:
        original = path.read_text()
    except OSError as err:
        raise ChainDefaultsStatusError(
            f"cannot read {CHAIN_DEFAULTS_PATH}: {err}"
        ) from err
    updated = _restamped_profile_text(
        original, plan.new_confirmed_commit, plan.new_confirmed_at
    )
    if not plan.fingerprint_plan.nothing_to_do:
        try:
            gate_staleness.write_fingerprint_store(
                project_root,
                gate_staleness.FingerprintStore(
                    confirmed_commit=plan.new_confirmed_commit,
                    confirmed_at=plan.new_confirmed_at,
                    fingerprints=plan.fingerprint_plan.fingerprints,
                ),
            )
        except (gate_staleness.GateStalenessError, OSError) as err:
            raise ChainDefaultsStatusError(
                f"failed to write the fingerprint store: {err}"
            ) from err
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp_path.write_text(updated)
        os.replace(tmp_path, path)
    except OSError as err:
        raise ChainDefaultsStatusError(
            f"failed to write {CHAIN_DEFAULTS_PATH} after writing the "
            f"fingerprint store ({err}); the store's stamp matches no profile, "
            "so user-scope targets stay fail-closed until a re-stamp succeeds"
        ) from err


def _restamp_payload(plan: RestampPlan, dry_run: bool) -> dict:
    return {
        "dry_run": dry_run,
        "previous_confirmed_commit": plan.previous_confirmed_commit,
        "new_confirmed_commit": plan.new_confirmed_commit,
        "new_confirmed_at": plan.new_confirmed_at,
        "staleness": (
            {
                "stale": plan.staleness.stale,
                "stale_files": [
                    {"path": f.path, "reason": f.reason}
                    for f in plan.staleness.stale_files
                ],
            }
            if plan.staleness is not None
            else None
        ),
        "staleness_error": plan.staleness_error,
        "fingerprints": {
            "nothing_to_do": plan.fingerprint_plan.nothing_to_do,
            "entries": [
                {
                    "name": e.name,
                    "path": str(e.absolute_path) if e.absolute_path else None,
                    "fingerprint": e.fingerprint,
                    "comparison": e.comparison,
                }
                for e in plan.fingerprint_plan.entries
            ],
        },
    }


def format_restamp_json(plan: RestampPlan, dry_run: bool) -> str:
    return json.dumps(_restamp_payload(plan, dry_run), indent=2)


def format_restamp_text(plan: RestampPlan, dry_run: bool) -> str:
    lines = ["Re-stamp (dry run, nothing written):" if dry_run else "Re-stamped:"]
    lines.append(
        f"  confirmed_commit: {plan.previous_confirmed_commit} -> "
        f"{plan.new_confirmed_commit}"
    )
    lines.append(f"  confirmed_at: {plan.new_confirmed_at}")
    lines.append("Stale files being re-confirmed:")
    if plan.staleness is not None:
        if plan.staleness.stale:
            for stale_file in plan.staleness.stale_files:
                lines.append(f"  - {stale_file.path}: {stale_file.reason}")
        else:
            lines.append("  (none -- not stale)")
    else:
        lines.append(f"  unavailable: {plan.staleness_error}")
    lines.append("Fingerprints (user-scope installed targets):")
    if plan.fingerprint_plan.nothing_to_do:
        lines.append("  nothing to fingerprint")
    else:
        for entry in plan.fingerprint_plan.entries:
            where = f" ({entry.absolute_path})" if entry.absolute_path else ""
            lines.append(f"  - {entry.comparison}: {entry.name}{where}")
        lines.append(
            "  note: only hashes are stored, so a `changed` entry shows that "
            "the content differs, not what changed"
        )
    if not dry_run:
        lines.append(
            "Skip consent is bound to this file's blob hash, so it is now "
            "invalid; re-grant it with /lrh-config-gates if needed."
        )
    return "\n".join(lines)
