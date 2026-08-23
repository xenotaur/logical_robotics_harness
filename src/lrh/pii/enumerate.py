"""Git-plumbing-based full-history path enumeration for `lrh pii scan`.

Enumerates every path ever added or renamed-into across all refs, then,
for an arbitrary subset of those paths, every commit that touched each
one - not only its add commit. This relies on git's own plumbing commands
rather than a bespoke blob-walking engine, per `PROP-LRH-PII-SCAN`
Decision 3.

`enumerate_commits_for_paths` takes an explicit path set rather than
assuming "Layer 1-flagged paths only", so a future all-text content scan
(`WI-PII-SCAN-LAYER2-CONTENT`) can request the same per-commit history for
every text path, not only ones this package's own Layer 1 detector
flagged (PR #596 review, `chatgpt-codex-connector` P1).

Both git invocations pass `-m` (show diffs for merge commits against
each parent, as if they were ordinary commits): plain `git log` suppresses
diffs for merge commits by default, so a path introduced only by a merge
commit's own tree (e.g. a conflict resolved by adding a new file) is
otherwise invisible to a path-status walk, even though `--all` visits the
merge commit itself.

Both invocations use `--name-status --find-renames` rather than
`--name-only`, and treat a rename's *destination* as the reportable path
at the commit that renamed it - a path that was renamed from something
benign to something suspicious (e.g. `notes.txt` to `passport.pdf`) must
be a candidate for Layer 1, not only literal add events (PR #616 review,
`chatgpt-codex-connector` P1). `enumerate_commits_for_paths` reports the
path as it actually existed in the tree at each returned commit, not the
caller's input path - a caller fetching content via
`git show <commit>:<path>` needs the pre-rename name for commits that
predate the rename, since the post-rename name did not exist yet at that
point in history (PR #616 review, `chatgpt-codex-connector` P1).

`-m` reports a merge commit's diff once per parent it differs from, so
`--follow -m` together can report the same commit more than once for a
single path (verified empirically); both functions deduplicate by commit
to keep their contract at "one entry per commit", not "one entry per
parent-diff".
"""

from __future__ import annotations

import dataclasses
import pathlib
import subprocess

_COMMIT_MARKER = "COMMIT "


@dataclasses.dataclass(frozen=True)
class PathCommit:
    """One commit that touched a given path, at the name that path had in
    the tree at that specific commit."""

    path: str
    commit: str


def _path_at_status_line(line: str) -> str | None:
    """Parse one `--name-status` line, returning the reportable path: the
    destination for a rename/copy (`R100\told\tnew`, `C100\told\tnew`), or
    the single path for any other status (`A\tpath`, `M\tpath`, ...)."""
    parts = line.split("\t")
    if not parts or not parts[0]:
        return None
    status = parts[0]
    if status.startswith("R") or status.startswith("C"):
        return parts[2] if len(parts) > 2 else None
    return parts[1] if len(parts) > 1 else None


def enumerate_added_paths(project_root: pathlib.Path) -> list[str]:
    """Return every path ever added or renamed-into across all refs,
    deduplicated and sorted.

    Uses `git log --all -m --diff-filter=AR --name-status --find-renames`.
    A rename is reported under its destination name, since that is the
    name Layer 1 needs to evaluate - the source name of a rename is only
    reportable if it was itself an add event in its own right.
    """
    result = subprocess.run(
        [
            "git",
            "-C",
            str(project_root),
            "log",
            "--all",
            "-m",
            "--diff-filter=AR",
            "--name-status",
            "--find-renames",
            "--pretty=format:",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    seen: dict[str, None] = {}
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        path = _path_at_status_line(line)
        if path:
            seen.setdefault(path, None)
    return sorted(seen)


def enumerate_commits_for_paths(
    project_root: pathlib.Path, paths: list[str]
) -> list[PathCommit]:
    """For each path in `paths`, return every commit that touched it across
    all refs, following renames - not only its add commit. Each result's
    `path` is the name that path had in the tree at that specific commit,
    not necessarily the input `path` (which predates any earlier rename).

    Accepts an arbitrary path set; the caller decides which paths need
    this (Layer 1-flagged paths by default, every text path under Layer
    2's `content_scan_scope: "all-text"`).

    Shells out to `git log` once per path - O(len(paths)) subprocesses.
    Acceptable for the flagged-paths default (small by construction), but
    a caller passing thousands of paths (e.g. `content_scan_scope:
    "all-text"` on a very large repo) will be slow; a batched/fast-path
    mode is deferred, matching this work item's own already-disclosed
    "full-history enumeration performance on very large repos is
    untested" risk note rather than a gap introduced here (PR #616
    review, `copilot-pull-request-reviewer`).
    """
    commits: list[PathCommit] = []
    for path in paths:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(project_root),
                "log",
                "--all",
                "-m",
                "--follow",
                "--find-renames",
                "--name-status",
                f"--pretty=format:{_COMMIT_MARKER}%H",
                "--",
                path,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        seen_commits: dict[str, str] = {}
        current_commit: str | None = None
        for raw_line in result.stdout.splitlines():
            if raw_line.startswith(_COMMIT_MARKER):
                current_commit = raw_line[len(_COMMIT_MARKER) :].strip()
                continue
            line = raw_line.strip()
            if not line or current_commit is None:
                continue
            path_at_commit = _path_at_status_line(line)
            if path_at_commit and current_commit not in seen_commits:
                seen_commits[current_commit] = path_at_commit
        commits.extend(
            PathCommit(path=path_at_commit, commit=commit)
            for commit, path_at_commit in seen_commits.items()
        )
    return commits
