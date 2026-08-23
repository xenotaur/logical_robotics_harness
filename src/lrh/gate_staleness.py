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
import json
import pathlib
import re
import subprocess

_MARKER_START = "<!-- GATE-DEFINITION -->"
_MARKER_END = "<!-- /GATE-DEFINITION -->"

_HUNK_HEADER_RE = re.compile(
    r"^@@ -(?P<old_start>\d+)(?:,(?P<old_count>\d+))? "
    r"\+(?P<new_start>\d+)(?:,(?P<new_count>\d+))? @@"
)

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
) -> FileStaleness:
    """Check one gate-bearing file for a semantic (marker-scoped) change."""
    old_content = _show_file_at(project_root, confirmed_commit, relative_path)
    new_content = _show_file_at(project_root, head, relative_path)

    if old_content is None and new_content is None:
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


def check_gate_staleness(
    project_root: pathlib.Path,
    confirmed_commit: str,
    head: str = "HEAD",
    watched_files: tuple[str, ...] = DEFAULT_WATCHED_FILES,
) -> StalenessResult:
    """Check every watched gate-bearing file for semantic staleness."""
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
    _run_git(
        ["rev-parse", "--verify", f"{confirmed_commit}^{{commit}}"], project_root
    )
    resolved_head = _run_git(["rev-parse", head], project_root).strip()
    files = tuple(
        check_file_staleness(project_root, confirmed_commit, resolved_head, path)
        for path in watched_files
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
