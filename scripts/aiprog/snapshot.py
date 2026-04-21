#!/usr/bin/env python3
"""Generate Markdown context packets from a project's control-plane files."""

from __future__ import annotations

import sys

from lrh.assist import snapshot_cli


def main(argv: list[str] | None = None) -> int:
    return snapshot_cli.run_snapshot_cli(
        argv=argv if argv is not None else sys.argv[1:],
        prog="snapshot.py",
    )


if __name__ == "__main__":
    raise SystemExit(main())
