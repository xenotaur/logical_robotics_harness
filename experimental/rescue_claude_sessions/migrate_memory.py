"""Copy an orphaned memory corpus from an old bucket to its canonical bucket.

Memory is path-keyed like transcripts: it lives at
``~/.claude/projects/<slug>/memory/``. When a repository's physical path
changes, sessions started under the new path resolve to a new slug with an
empty ``memory/``, and every previously learned fact goes silently unread.

This tool *copies* rather than moves, so the old corpus stays as a rollback
until new-path sessions are observed consuming the migrated one. Every copied
file is verified by SHA-256 before the run is called a success.

Dry-run by default; pass --apply to write.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import bucketlib


def plan_copy(source: Path, dest: Path) -> tuple[list[Path], list[Path]]:
    """Return (files to copy, files already present at dest)."""
    to_copy: list[Path] = []
    collisions: list[Path] = []
    for item in sorted(source.rglob("*")):
        if not item.is_file():
            continue
        target = dest / item.relative_to(source)
        if target.exists():
            collisions.append(item)
        else:
            to_copy.append(item)
    return to_copy, collisions


def migrate(
    old: bucketlib.Bucket,
    new: bucketlib.Bucket,
    *,
    apply: bool,
    allow_merge: bool,
) -> int:
    source = old.memory_dir
    dest = new.memory_dir

    if not source.is_dir():
        print(f"  skip: no memory corpus at {source}")
        return 0
    files = [p for p in source.rglob("*") if p.is_file()]
    if not files:
        print(f"  skip: memory corpus at {source} is empty")
        return 0

    dest_existing = [p for p in dest.rglob("*") if p.is_file()] if dest.is_dir() else []
    if dest_existing and not allow_merge:
        print(
            f"  REFUSE: destination already holds {len(dest_existing)} file(s):\n"
            f"          {dest}\n"
            f"          re-run with --allow-merge if you intend to merge"
        )
        return 1

    to_copy, collisions = plan_copy(source, dest)
    print(f"  source : {source}  ({len(files)} files)")
    print(f"  dest   : {dest}")
    print(f"  copy   : {len(to_copy)} file(s)")
    if collisions:
        print(f"  keep   : {len(collisions)} existing destination file(s) left untouched")

    if not apply:
        print("  (dry run - nothing written; pass --apply to copy)")
        return 0

    dest.mkdir(parents=True, exist_ok=True)
    for item in to_copy:
        target = dest / item.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)

    mismatched: list[str] = []
    for item in to_copy:
        target = dest / item.relative_to(source)
        if not target.exists():
            mismatched.append(f"missing: {target}")
        elif bucketlib.sha256_file(item) != bucketlib.sha256_file(target):
            mismatched.append(f"hash mismatch: {target}")

    if mismatched:
        print(f"  FAILED verification ({len(mismatched)}):")
        for line in mismatched[:10]:
            print(f"    {line}")
        return 1

    print(f"  verified: {len(to_copy)} file(s) match by SHA-256")
    index = dest / "MEMORY.md"
    if index.exists():
        lines = index.read_text(encoding="utf-8", errors="replace").count("\n")
        print(f"  MEMORY.md present at destination ({lines} lines)")
    else:
        print("  WARNING: no MEMORY.md at destination - the index drives recall")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--alias",
        action="append",
        default=None,
        metavar="OLD=NEW",
        help="filesystem prefix move, repeatable "
        f"(default: {' '.join(bucketlib.DEFAULT_ALIASES)})",
    )
    parser.add_argument(
        "--only",
        action="append",
        default=None,
        metavar="SUBSTRING",
        help="restrict to buckets whose name contains SUBSTRING, repeatable",
    )
    parser.add_argument("--apply", action="store_true", help="actually copy (default: dry run)")
    parser.add_argument(
        "--allow-merge",
        action="store_true",
        help="proceed even when the destination corpus is non-empty",
    )
    args = parser.parse_args()

    raw = args.alias or list(bucketlib.DEFAULT_ALIASES)
    aliases = [bucketlib.parse_alias(item) for item in raw]

    buckets = bucketlib.load_buckets()
    pairs = bucketlib.pair_buckets(buckets, aliases)

    failures = 0
    handled = 0
    for old, expected, new in pairs:
        if args.only and not any(token in old.name for token in args.only):
            continue
        if old.memory_count() <= 0:
            continue
        print(f"\n{old.name}")
        if new is None:
            print(f"  skip: destination bucket does not exist yet ({expected})")
            print("        start one session from the new path first, then re-run")
            continue
        handled += 1
        failures += migrate(old, new, apply=args.apply, allow_merge=args.allow_merge)

    print(f"\n{handled} corpus/corpora considered, {failures} failure(s)")
    if handled and not args.apply:
        print("Re-run with --apply to perform the copy.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
