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
#: installed targets are stored, relative to `project_root`. Written by
#: `record_fingerprints` at consent-grant time; read by `check_gate_staleness`
#: for any watch target that resolves outside `project_root`'s working tree,
#: where no git history exists to diff against `confirmed_commit`.
FINGERPRINT_PATH = "project/config/chain-defaults-fingerprints.json"


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
    the actually-installed skill target by reusing
    `lrh.skills.installer`'s own install-planning logic, and watch the
    resolved paths there instead -- using `INSTALLED_CANONICAL_SKILL_NAMES`
    by default (never `_`-prefixed directories, which the installer itself
    never copies) unless `canonical_names` overrides it explicitly. Each
    resolved path is classified as `"git"` (inside `project_root`'s working
    tree -- e.g. a project-local installed target committed to that repo)
    or `"fingerprint"` (outside it -- e.g. the documented default user-scope
    install under `Path.home()`, which has no git history to diff against
    at all).

    If the installed target itself can't be resolved, every canonical skill
    is returned as `"unresolved"` -- `check_gate_staleness`'s fail-closed
    requirement, not a caller error.
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
        claude_targets = [
            t for t in install_targets if t.target is installer.SkillTarget.CLAUDE
        ]
        chosen = claude_targets[0] if claude_targets else install_targets[0]
    except (installer.SkillSourceError, ValueError, IndexError, OSError):
        chosen = None

    if chosen is None:
        return tuple(
            WatchTarget(canonical_name=name, kind="unresolved") for name in names
        )

    resolved: list[WatchTarget] = []
    for name in names:
        absolute_path = chosen.skills_dir / name
        try:
            relative_path = absolute_path.relative_to(project_root)
        except ValueError:
            resolved.append(
                WatchTarget(
                    canonical_name=name,
                    kind="fingerprint",
                    absolute_path=absolute_path,
                )
            )
        else:
            resolved.append(
                WatchTarget(
                    canonical_name=name,
                    kind="git",
                    relative_path=str(relative_path),
                    strict_absence=True,
                )
            )
    return tuple(resolved)


def compute_fingerprint(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def load_fingerprints(project_root: pathlib.Path) -> dict[str, str] | None:
    """Load persisted content fingerprints, or None if unavailable.

    Returns None (never raises) on a missing, unreadable, or malformed
    file -- `check_gate_staleness` treats a None return as "no fingerprint
    on record for any untracked target" and fails every such target closed,
    rather than surfacing this as a hard error.
    """
    path = project_root / FINGERPRINT_PATH
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return {str(key): str(value) for key, value in data.items()}


def record_fingerprints(
    project_root: pathlib.Path,
    targets: tuple[WatchTarget, ...],
) -> dict[str, str]:
    """Compute and persist current-content fingerprints for untracked targets.

    Intended to run at `skip_if_opted_in` consent-grant time, alongside
    stamping `confirmed_commit`, for every target `resolve_watch_targets`
    classified `"fingerprint"` (outside `project_root`'s working tree).
    Raises if a target file is missing -- a consent grant must not silently
    record an empty/partial fingerprint set.
    """
    fingerprints: dict[str, str] = {}
    for target in targets:
        if target.kind != "fingerprint":
            continue
        if target.absolute_path is None or not target.absolute_path.is_file():
            raise GateStalenessError(
                f"cannot fingerprint missing installed target: "
                f"{target.canonical_name} ({target.absolute_path})"
            )
        fingerprints[target.canonical_name] = compute_fingerprint(
            target.absolute_path.read_bytes()
        )
    path = project_root / FINGERPRINT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(fingerprints, indent=2, sort_keys=True) + "\n"
    # Atomic write: a temp file in the same directory (so the rename is on
    # the same filesystem), then os.replace -- a process interrupted
    # mid-write must never leave a partial/corrupt fingerprint file behind,
    # since `load_fingerprints` treats any unreadable file as "no
    # fingerprint on record" and fails every untracked target closed.
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(payload, encoding="utf-8")
    os.replace(tmp_path, path)
    return fingerprints


def check_target_staleness(
    project_root: pathlib.Path,
    confirmed_commit: str,
    head: str,
    target: WatchTarget,
    fingerprints: dict[str, str] | None,
) -> FileStaleness:
    """Check one resolved `WatchTarget` for staleness, by whichever means
    its `kind` supports."""
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
    current = compute_fingerprint(target.absolute_path.read_bytes())
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
    _run_git(["rev-parse", "--verify", f"{confirmed_commit}^{{commit}}"], project_root)
    resolved_head = _run_git(["rev-parse", head], project_root).strip()

    if watched_files is not None:
        files = tuple(
            check_file_staleness(project_root, confirmed_commit, resolved_head, path)
            for path in watched_files
        )
    else:
        targets = resolve_watch_targets(project_root)
        fingerprints = load_fingerprints(project_root)
        files = tuple(
            check_target_staleness(
                project_root, confirmed_commit, resolved_head, target, fingerprints
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
