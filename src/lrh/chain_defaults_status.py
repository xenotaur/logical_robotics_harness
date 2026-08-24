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
import json
import pathlib
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


def _run_git(args: list[str], project_root: pathlib.Path) -> subprocess.CompletedProcess:
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
    result = _run_git(["config", "--local", "--get", CONSENT_HASH_CONFIG_KEY], project_root)
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

    current_hash = hash_object(project_root, CHAIN_DEFAULTS_PATH) if profile_exists else ""
    stored_hash = read_consent_hash(project_root)
    consent = ConsentStatus(
        stored_hash=stored_hash,
        current_hash=current_hash,
        valid=bool(profile_exists and stored_hash is not None and stored_hash == current_hash),
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
            )
        except gate_staleness.GateStalenessError as err:
            staleness_error = str(err)
    else:
        staleness_error = "confirmed_commit is null/absent -- no prior confirmation on record"

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
