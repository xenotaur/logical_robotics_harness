"""Shared helpers for finding and validating Codex export directories.

``/lrh-codex-export``'s routine capture path writes each export under a
private ``mktemp -d`` directory (see
``src/lrh/skills/lrh-codex-export/SKILL.md`` Step 2), which on macOS resolves
under ``/var/folders/.../T/...`` -- OS-managed scratch that can be reclaimed
at any time. This module is read-only: it locates candidate export
directories under an arbitrary root and classifies each as valid, partial, or
empty, without ever writing anything.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

# The skill always names the leaf directory this way (SKILL.md Step 2:
# ``lrh-codex-export-$EXPORT_ID.XXXXXX``); matching by name first is a cheap
# pre-filter before opening any file.
EXPORT_DIR_NAME_PREFIX = "lrh-codex-export-"

# Both files the skill always writes into a successful export directory
# (SKILL.md Step 2: ``$EXPORT_DIR/export.md``, ``$EXPORT_DIR/raw.json``).
EXPORT_MARKDOWN_NAME = "export.md"
EXPORT_RAW_NAME = "raw.json"

# The durable private archive location the skill itself already documents as
# the alternative to ephemeral capture (SKILL.md Step 2, "If the user wants a
# durable private archive instead of an ephemeral dogfood capture...").
DEFAULT_DEST_ROOT = Path("~/.lrh/private/codex").expanduser()


def default_source_root() -> Path:
    """Mirror the skill's own ``${TMPDIR:-/tmp}`` fallback (SKILL.md Step 2)."""
    raw = os.environ.get("TMPDIR", "/tmp")
    return Path(raw)


@dataclass(frozen=True)
class ExportCandidate:
    """One directory matching the export-directory name pattern."""

    path: Path
    status: str  # "valid" | "missing_export_md" | "missing_raw_json" | "empty"
    issues: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return self.status == "valid"


def find_export_dirs(root: Path) -> list[Path]:
    """Recursively find directories whose name matches the export pattern.

    Matches at any depth, not just directly under ``root`` -- captured
    exports have been observed at both a flat ``root/lrh-codex-export-*/``
    depth and nested under other temp-directory layouts (e.g.
    ``root/tmp*/archive/codex/exports/YYYY/MM/lrh-codex-export-*-thread-*/``).
    A name match alone does not imply validity; see ``classify_export_dir``.
    """
    root = root.expanduser()
    if not root.is_dir():
        return []
    found: list[Path] = []
    for dirpath, dirnames, _filenames in os.walk(root):
        for name in dirnames:
            if name.lower().startswith(EXPORT_DIR_NAME_PREFIX):
                found.append(Path(dirpath) / name)
    return sorted(found)


def classify_export_dir(path: Path) -> ExportCandidate:
    """Classify a candidate directory without reading transcript content.

    Deliberately does not parse ``export.md``'s frontmatter or ``raw.json``'s
    structure -- that validation belongs to
    ``lrh.conversations.export_inspector`` (the production inspector this
    tool does not import, to keep this directory dependency-free like its
    ``rescue_claude_sessions`` sibling). This is a structural check only:
    are the two files the skill always writes actually present and
    non-empty, so an aborted or partial capture cannot be mistaken for a
    successful one.
    """
    issues: list[str] = []
    export_md = path / EXPORT_MARKDOWN_NAME
    raw_json = path / EXPORT_RAW_NAME

    entries = list(path.iterdir()) if path.is_dir() else []
    if not entries:
        return ExportCandidate(
            path=path, status="empty", issues=("directory is empty",)
        )

    if not export_md.is_file() or export_md.stat().st_size == 0:
        issues.append(f"missing or empty {EXPORT_MARKDOWN_NAME}")
    if not raw_json.is_file() or raw_json.stat().st_size == 0:
        issues.append(f"missing or empty {EXPORT_RAW_NAME}")

    if not issues:
        return ExportCandidate(path=path, status="valid", issues=())
    if any(EXPORT_MARKDOWN_NAME in issue for issue in issues):
        status = "missing_export_md"
    else:
        status = "missing_raw_json"
    return ExportCandidate(path=path, status=status, issues=tuple(issues))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pluralize_directories(count: int) -> str:
    return "directory" if count == 1 else "directories"


def is_unsafe_pair(source: Path, dest: Path) -> bool:
    """True if ``source`` and ``dest`` are equal or one nests inside the other.

    Once both roots are caller-supplied (rather than one being a fixed,
    always-disjoint default), a re-run or a typo could point them at
    overlapping trees -- e.g. re-running against an already-migrated
    directory, or passing ``--dest`` as a subdirectory of ``--source`` by
    mistake. Mirrors the belt-and-suspenders path guard already used for
    ``--raw-out`` in ``src/lrh/conversations/codex_app_server_export.py``
    (``_reject_unsafe_raw_output_path``).
    """
    source = source.expanduser().resolve()
    dest = dest.expanduser().resolve()
    if source == dest:
        return True
    return source in dest.parents or dest in source.parents
