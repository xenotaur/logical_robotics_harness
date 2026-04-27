"""Build artifact cleanup for LRH development workflows."""

from __future__ import annotations

import argparse
import pathlib
import shutil
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Remove generated build artifacts used by packaging workflows.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print cleanup actions without deleting files.",
    )
    return parser


def _artifact_paths() -> list[pathlib.Path]:
    return [
        REPO_ROOT / "build",
        REPO_ROOT / "dist",
        REPO_ROOT / "lrh.egg-info",
    ]


def clean(*, dry_run: bool = False) -> int:
    """Remove conservative build artifact paths if present."""
    for artifact_path in _artifact_paths():
        if not artifact_path.exists():
            print(f"skip (missing): {artifact_path.relative_to(REPO_ROOT)}")
            continue

        print(f"remove: {artifact_path.relative_to(REPO_ROOT)}")
        if dry_run:
            continue
        if artifact_path.is_dir():
            shutil.rmtree(artifact_path)
        else:
            artifact_path.unlink()

    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        return clean(dry_run=args.dry_run)
    except OSError as error:
        print(f"ERROR: cleanup failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
