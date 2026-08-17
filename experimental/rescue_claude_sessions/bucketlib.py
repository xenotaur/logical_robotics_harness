"""Shared helpers for reading Claude Code project buckets as path-keyed state.

A *bucket* is one directory under ``~/.claude/projects``. Its name is the
session's working directory with every non-alphanumeric character replaced by
``-``, so a repository that gains a second path spelling (a symlink, a move)
gains a second bucket holding its own transcripts and its own ``memory/``.

This module is read-only. Mutating tools live in the sibling scripts.
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path


# Claude Code truncates slugs past this length and appends a hash of the full
# path, which we cannot reproduce; pairing is unreliable at or beyond it.
SLUG_TRUNCATION_LIMIT = 200

DEFAULT_ALIASES = ("~/Workspace=~/Tempspace/Projects",)


def config_root() -> Path:
    """Return the Claude config directory, honoring CLAUDE_CONFIG_DIR."""
    return Path(os.environ.get("CLAUDE_CONFIG_DIR", "~/.claude")).expanduser()


def projects_root() -> Path:
    return config_root() / "projects"


def lrh_archive_root() -> Path:
    """Return LRH's durable session-archive root.

    Mirrors the default used by ``lrh sessions sync``: ``$LRH_SESSION_ARCHIVE_ROOT``
    if set, else ``~/.local/share/lrh/session-archive``. That archive, not this
    tooling, is the durable record; see plan.md.
    """
    raw = os.environ.get("LRH_SESSION_ARCHIVE_ROOT")
    if raw:
        return Path(raw).expanduser()
    return Path("~/.local/share/lrh/session-archive").expanduser()


def archived_copy(transcript: Path) -> Path:
    """Where ``lrh sessions sync`` would mirror this transcript."""
    return lrh_archive_root() / "raw" / transcript.parent.name / transcript.name


def slugify(path: str | Path) -> str:
    """Convert a filesystem path to its bucket directory name."""
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


@dataclass(frozen=True)
class Bucket:
    """One project identity on disk."""

    name: str
    path: Path

    @property
    def memory_dir(self) -> Path:
        return self.path / "memory"

    def transcripts(self) -> list[Path]:
        return sorted(self.path.glob("*.jsonl"))

    def memory_files(self) -> list[Path]:
        if not self.memory_dir.is_dir():
            return []
        return sorted(self.memory_dir.glob("*.md"))

    def memory_count(self) -> int:
        """Number of memory files, or -1 when the directory is absent."""
        if not self.memory_dir.is_dir():
            return -1
        return len(self.memory_files())

    def truncated_slug(self) -> bool:
        return len(self.name) >= SLUG_TRUNCATION_LIMIT


def load_buckets(root: Path | None = None) -> dict[str, Bucket]:
    root = root or projects_root()
    if not root.is_dir():
        return {}
    return {
        entry.name: Bucket(entry.name, entry)
        for entry in sorted(root.iterdir())
        if entry.is_dir()
    }


def parse_alias(raw: str) -> tuple[Path, Path]:
    """Parse an ``OLD=NEW`` filesystem-prefix alias."""
    if "=" not in raw:
        raise ValueError(f"alias must be OLD=NEW, got {raw!r}")
    old, new = raw.split("=", 1)
    return (
        Path(old).expanduser(),
        Path(new).expanduser(),
    )


def pair_buckets(
    buckets: dict[str, Bucket],
    aliases: list[tuple[Path, Path]],
) -> list[tuple[Bucket, str, Bucket | None]]:
    """Pair each old-root bucket with its canonical new-root counterpart.

    Returns ``(old_bucket, expected_new_name, new_bucket_or_None)`` triples.
    Pairing is purely lexical on the slug, which is exactly how Claude Code
    derives the directory in the first place.
    """
    pairs: list[tuple[Bucket, str, Bucket | None]] = []
    for old_root, new_root in aliases:
        old_prefix = slugify(old_root)
        new_prefix = slugify(new_root)
        for name, bucket in buckets.items():
            if not name.startswith(old_prefix + "-"):
                continue
            expected = new_prefix + name[len(old_prefix) :]
            pairs.append((bucket, expected, buckets.get(expected)))
    return pairs


def index_sessions(buckets: dict[str, Bucket]) -> dict[str, list[Path]]:
    """Map session id to every transcript file bearing that id."""
    index: dict[str, list[Path]] = {}
    for bucket in buckets.values():
        for transcript in bucket.transcripts():
            index.setdefault(transcript.stem, []).append(transcript)
    return index


def split_sessions(buckets: dict[str, Bucket]) -> dict[str, list[Path]]:
    """Sessions whose id appears in more than one bucket."""
    return {
        session_id: paths
        for session_id, paths in index_sessions(buckets).items()
        if len(paths) > 1
    }


def sha256_file(path: Path, *, limit: int | None = None) -> str:
    """Hash a file, optionally only its first ``limit`` bytes."""
    digest = hashlib.sha256()
    remaining = limit
    with path.open("rb") as handle:
        while True:
            want = 1 << 20 if remaining is None else min(1 << 20, remaining)
            if want == 0:
                break
            chunk = handle.read(want)
            if not chunk:
                break
            digest.update(chunk)
            if remaining is not None:
                remaining -= len(chunk)
    return digest.hexdigest()


def is_byte_prefix(shorter: Path, longer: Path) -> bool:
    """True when ``shorter`` is a byte-exact prefix of ``longer``.

    ``cmp -n`` is unreliable here: BSD cmp reports EOF and exits non-zero for a
    pure prefix relationship, which reads as a difference when it is not one.
    Hashing the prefix has no such ambiguity.
    """
    short_size = shorter.stat().st_size
    if short_size > longer.stat().st_size:
        return False
    return sha256_file(shorter) == sha256_file(longer, limit=short_size)


def count_lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(chunk.count(b"\n") for chunk in iter(lambda: handle.read(1 << 20), b""))
