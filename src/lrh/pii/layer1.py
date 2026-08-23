"""Layer 1 file-type/path/filename heuristic detector for `lrh pii scan`.

Flags a path as suspicious based on its extension/glob or filename
keywords - not its content. This is deliberately the primary signal
(`PROP-LRH-PII-SCAN` Decision 2): an entire misplaced document can be
flagged even if it contains zero regex-matchable content, which is the
failure mode a content-only scanner cannot catch.
"""

from __future__ import annotations

import dataclasses
import fnmatch
import pathlib

from lrh.pii import config as pii_config


@dataclasses.dataclass(frozen=True)
class Layer1Finding:
    path: str
    rule_id: str
    matched_glob: str | None
    matched_keyword: str | None


def flag_path(path: str, config: pii_config.PiiConfig) -> Layer1Finding | None:
    """Return a `Layer1Finding` if `path` matches a configured glob or
    filename keyword, else `None`. Glob checks run first; a path matching
    both a glob and a keyword is reported once, under the glob rule.

    Glob matching runs against the full, normalized repo-relative path
    (not only the basename), so a directory-qualified rule like
    `private/*.txt` can match - a plain extension glob like `*.pdf` still
    matches regardless of directory, since `fnmatch`'s `*` matches `/`
    too (PR #616 review, `chatgpt-codex-connector` P2 /
    `copilot-pull-request-reviewer`). Filename-keyword matching still runs
    against the basename only - a keyword like "statement" is about the
    filename itself, not any directory component that happens to contain
    it.

    Both glob and keyword matching are case-insensitive (`fnmatch.fnmatch`
    is only case-insensitive on platforms where `os.path.normcase` folds
    case, which is not POSIX - matching a realistic `Statement.PDF` from a
    Windows-originated scan requires explicitly lowercasing both sides)."""
    normalized_path = pathlib.PurePosixPath(path).as_posix().lower()
    name_lower = pathlib.PurePosixPath(path).name.lower()

    for glob in config.path_globs:
        if fnmatch.fnmatch(normalized_path, glob.lower()):
            return Layer1Finding(
                path=path,
                rule_id=f"path_glob.{glob}",
                matched_glob=glob,
                matched_keyword=None,
            )

    for keyword in config.filename_keywords:
        if keyword.lower() in name_lower:
            return Layer1Finding(
                path=path,
                rule_id=f"filename_keyword.{keyword}",
                matched_glob=None,
                matched_keyword=keyword,
            )

    return None


def flag_paths(paths: list[str], config: pii_config.PiiConfig) -> list[Layer1Finding]:
    """Return a `Layer1Finding` for every path in `paths` that matches a
    configured glob or filename keyword."""
    findings = []
    for path in paths:
        finding = flag_path(path, config)
        if finding is not None:
            findings.append(finding)
    return findings
