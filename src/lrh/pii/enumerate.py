"""Git-plumbing-based full-history path enumeration for `lrh pii scan`.

Enumerates every path ever added across all refs, then, for an arbitrary
subset of those paths, every commit that touched each one - not only its
add commit. This relies on git's own plumbing commands rather than a
bespoke blob-walking engine, per `PROP-LRH-PII-SCAN` Decision 3.

`enumerate_commits_for_paths` takes an explicit path set rather than
assuming "Layer 1-flagged paths only", so a future all-text content scan
(`WI-PII-SCAN-LAYER2-CONTENT`) can request the same per-commit history for
every text path, not only ones this package's own Layer 1 detector
flagged (PR #596 review, `chatgpt-codex-connector` P1).

Both git invocations pass `-m` (show diffs for merge commits against
each parent, as if they were ordinary commits): plain `git log` suppresses
diffs for merge commits by default, so a path introduced only by a merge
commit's own tree (e.g. a conflict resolved by adding a new file) is
otherwise invisible to `--diff-filter=A` and to a per-path history walk,
even though `--all` visits the merge commit itself. Verified empirically
against a scratch repo before this fix landed - the WI's own review
caught this.

`-m` reports a merge commit's diff once per parent it differs from,
so `--follow -m` together can report the same commit hash more than once
for a single path (verified empirically) - `enumerate_commits_for_paths`
deduplicates per path to keep its contract at "one entry per commit that
touched this path", not "one entry per parent-diff that touched it".
"""

from __future__ import annotations

import dataclasses
import pathlib
import subprocess


@dataclasses.dataclass(frozen=True)
class PathCommit:
    """One commit that touched a given path, at its current name."""

    path: str
    commit: str


def enumerate_added_paths(project_root: pathlib.Path) -> list[str]:
    """Return every path ever added across all refs, deduplicated and sorted.

    Uses `git log --all --diff-filter=A --name-only` - the path reported is
    the name the file had at the commit that added it, not necessarily its
    current name if it was later renamed.
    """
    result = subprocess.run(
        [
            "git",
            "-C",
            str(project_root),
            "log",
            "--all",
            "-m",
            "--diff-filter=A",
            "--name-only",
            "--pretty=format:",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    seen: dict[str, None] = {}
    for line in result.stdout.splitlines():
        path = line.strip()
        if path:
            seen.setdefault(path, None)
    return sorted(seen)


def enumerate_commits_for_paths(
    project_root: pathlib.Path, paths: list[str]
) -> list[PathCommit]:
    """For each path in `paths`, return every commit that touched it across
    all refs, following renames - not only its add commit.

    Accepts an arbitrary path set; the caller decides which paths need
    this (Layer 1-flagged paths by default, every text path under Layer
    2's `content_scan_scope: "all-text"`).
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
                "--format=%H",
                "--",
                path,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        seen_for_path: dict[str, None] = {}
        for line in result.stdout.splitlines():
            commit = line.strip()
            if commit:
                seen_for_path.setdefault(commit, None)
        commits.extend(PathCommit(path=path, commit=commit) for commit in seen_for_path)
    return commits
