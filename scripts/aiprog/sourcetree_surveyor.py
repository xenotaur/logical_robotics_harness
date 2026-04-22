#!/usr/bin/env python3
"""Compatibility wrapper for the migrated assist sourcetree surveyor module."""

from __future__ import annotations

import pathlib
import sys
from importlib import import_module


def _ensure_src_on_sys_path() -> None:
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    src_dir = repo_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))


if __name__ == "__main__":
    _ensure_src_on_sys_path()
    sourcetree_surveyor = import_module("lrh.assist.sourcetree_surveyor")
    raise SystemExit(sourcetree_surveyor.main(sys.argv[1:]))
