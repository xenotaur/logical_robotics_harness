#!/usr/bin/env python3
"""Legacy compatibility entry point for snapshot generation.

Prefer `lrh snapshot ...` for day-to-day usage.
"""

from __future__ import annotations

import sys

from lrh.assist import snapshot_cli


def main(argv: list[str] | None = None) -> int:
    return snapshot_cli.run_snapshot_cli(
        argv=argv if argv is not None else sys.argv[1:],
        prog=(
            "scripts/aiprog/snapshot.py "
            "(legacy compatibility path; prefer `lrh snapshot`)"
        ),
    )


if __name__ == "__main__":
    raise SystemExit(main())
