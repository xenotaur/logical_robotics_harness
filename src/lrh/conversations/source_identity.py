"""Read an export source file together with a stable identity for it."""

from __future__ import annotations

import os
from pathlib import Path


def read_bytes_with_identity(path: Path) -> tuple[bytes, os.stat_result]:
    """Return the bytes of ``path`` and the ``os.stat_result`` of the file read.

    The identity is taken from the descriptor the bytes are read through, not
    from the pathname afterwards. A writer that must never truncate the file it
    just read compares its output descriptor against this identity with
    ``os.path.samestat``; unlike a later ``path.stat()``, it still describes
    the original file if the pathname is renamed, replaced, or removed between
    the read and the write.

    ``OSError`` propagates so each caller keeps its own error mapping.
    """
    fd = os.open(str(path), os.O_RDONLY)
    try:
        identity = os.fstat(fd)
        with os.fdopen(fd, "rb", closefd=False) as handle:
            data = handle.read()
    finally:
        os.close(fd)
    return data, identity
