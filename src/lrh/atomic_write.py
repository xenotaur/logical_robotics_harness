"""Shared atomic-write primitives, extracted from ``prompt_workflow_sessions``.

Used by any module that must never leave a destination file truncated or
partially written on interruption -- a plain ``write_text()``/``write_bytes()``
truncates the destination before writing, so a crash mid-write can silently
erase previously-good content. Writing to a temp file in the same directory
and renaming into place is atomic on POSIX (and ``os.replace`` is atomic on
Windows too), so readers only ever see the old complete content or the new
complete content, never a partial write.
"""

from __future__ import annotations

import contextlib
import os
import pathlib
import tempfile


def atomic_write(path: pathlib.Path, content: str) -> None:
    """Write ``content`` (text) to ``path`` without ever leaving a truncated file."""

    fd, tmp_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(tmp_name, path)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.remove(tmp_name)
        raise


def atomic_write_bytes(path: pathlib.Path, content: bytes) -> None:
    """Byte-mode counterpart of :func:`atomic_write`.

    For content copied verbatim (not re-serialized), avoiding a text
    round-trip that could alter encoding-sensitive bytes. Same atomicity
    guarantee as :func:`atomic_write`.
    """

    fd, tmp_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
        os.replace(tmp_name, path)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.remove(tmp_name)
        raise
