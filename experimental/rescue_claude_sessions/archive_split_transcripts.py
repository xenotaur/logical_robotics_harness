"""Archive stale duplicate transcripts left behind by a repository move.

When the same session id exists in two buckets, Claude Code's own resume path
degrades: the picker groups duplicate entries under one row, and cross-project
resume by id resolves "only when exactly one other project holds a transcript
with messages for it", so a duplicate makes ``--resume <id>`` report not-found
rather than pick a copy.

A stale copy is only safe to archive when it is a byte-exact *prefix* of the
longest copy, i.e. it holds no unique content. This tool proves that with
SHA-256 before touching anything, and refuses on genuine divergence.

Note ``cmp -n <size>`` is not a valid prefix test: BSD cmp reports EOF and exits
non-zero for a pure prefix, which reads as a difference when it is not one.

Files are moved to an archive directory, never deleted. Dry-run by default.
"""

from __future__ import annotations

import argparse
import os
import shutil
import time
from pathlib import Path

import bucketlib


def default_archive_dir() -> str:
    """Staging location for displaced copies.

    ``experimental/README.md`` asks for raw captures under ``/private/tmp``,
    which exists on macOS. Elsewhere that path is usually absent and not
    creatable by a normal user, so fall back to the platform temp dir. This is
    staging only — durability belongs to ``lrh sessions sync``.
    """
    if Path("/private/tmp").is_dir():
        return "/private/tmp/claude-rescue-archive"
    # `.get(k, default)` substitutes only when TMPDIR is *absent*; a
    # set-but-empty TMPDIR would yield a relative path and stage private
    # transcripts under the caller's cwd. `or` matches bash's ${TMPDIR:-/tmp}.
    return str(Path(os.environ.get("TMPDIR") or "/tmp") / "claude-rescue-archive")


LIVE_WINDOW_SECONDS = 300


def choose_keeper(
    paths: list[Path], new_prefixes: list[str]
) -> tuple[Path | None, str]:
    """Pick the copy to keep: longest wins; ties go to the canonical bucket."""
    ordered = sorted(paths, key=lambda p: p.stat().st_size, reverse=True)
    largest = ordered[0].stat().st_size
    tied = [p for p in ordered if p.stat().st_size == largest]
    if len(tied) == 1:
        return tied[0], "longest copy"
    canonical = [
        p
        for p in tied
        if any(bucketlib.matches_root(p.parent.name, pre) for pre in new_prefixes)
    ]
    if len(canonical) == 1:
        return canonical[0], "identical copies; kept the canonical bucket"
    return None, f"{len(tied)} identical copies, none uniquely canonical"


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
        "--archive-dir",
        default=default_archive_dir(),
        help=f"where to move stale copies (default {default_archive_dir()})",
    )
    parser.add_argument(
        "--apply", action="store_true", help="actually move (default: dry run)"
    )
    parser.add_argument(
        "--force-live",
        action="store_true",
        help=f"archive even if modified within {LIVE_WINDOW_SECONDS}s "
        "(a live session may be writing)",
    )
    parser.add_argument(
        "--no-require-archived",
        action="store_true",
        help="skip the precondition that LRH's durable archive already holds the copy "
        "(run 'lrh sessions sync' first; this tool's own archive dir is not durable)",
    )
    args = parser.parse_args()

    raw = args.alias or list(bucketlib.DEFAULT_ALIASES)
    aliases = [bucketlib.parse_alias(item) for item in raw]
    new_prefixes = [bucketlib.slugify(new) for _, new in aliases]

    buckets = bucketlib.load_buckets()
    splits = bucketlib.split_sessions(buckets)
    if not splits:
        print("no split sessions found")
        return 0

    stamp = time.strftime("%Y%m%d-%H%M%S")
    archive_root = Path(args.archive_dir).expanduser() / stamp

    staged: list[tuple[Path, Path]] = []
    refused = 0
    now = time.time()

    for session_id, paths in sorted(splits.items()):
        keeper, why = choose_keeper(paths, new_prefixes)
        print(f"\n{session_id}")
        if keeper is None:
            print(f"  REFUSE: {why}")
            refused += 1
            continue
        print(f"  keep   : {keeper.parent.name}  ({why})")

        for path in sorted(paths):
            if path == keeper:
                continue
            if not bucketlib.is_byte_prefix(path, keeper):
                print(
                    f"  REFUSE : {path.parent.name} is NOT a byte-exact prefix"
                    " - divergent content"
                )
                refused += 1
                continue
            if not args.no_require_archived:
                mirrored = bucketlib.archived_copy(path)
                if not mirrored.exists():
                    print(
                        f"  REFUSE : {path.parent.name} is not in LRH's"
                        " durable archive yet\n"
                        f"           expected {mirrored}\n"
                        f"           run 'lrh sessions sync' first, then re-run"
                    )
                    refused += 1
                    continue
                if not bucketlib.is_byte_prefix(path, mirrored):
                    print(
                        f"  REFUSE : {path.parent.name} differs from its"
                        f" archived copy at {mirrored}"
                    )
                    refused += 1
                    continue
            age = now - path.stat().st_mtime
            if age < LIVE_WINDOW_SECONDS and not args.force_live:
                print(
                    f"  REFUSE : {path.parent.name} modified {int(age)}s ago; "
                    f"a live session may be writing (use --force-live to override)"
                )
                refused += 1
                continue
            print(
                f"  archive: {path.parent.name}  (byte-exact prefix, no unique content)"
            )
            staged.append((path, archive_root / path.parent.name / path.name))

    print(f"\n{len(staged)} file(s) to archive, {refused} refusal(s)")
    if not staged:
        return 1 if refused else 0

    if not args.apply:
        print(f"(dry run - nothing moved; would archive under {archive_root})")
        print("Re-run with --apply to move.")
        return 0

    for source, target in staged:
        target.parent.mkdir(parents=True, exist_ok=True)
        digest = bucketlib.sha256_file(source)
        shutil.move(str(source), str(target))
        if bucketlib.sha256_file(target) != digest:
            print(f"  FAILED: hash changed while moving {source}")
            return 1
        print(f"  moved: {target}")

    print(f"\narchived {len(staged)} file(s) under {archive_root}")
    print("Nothing was deleted; restore by moving files back to their bucket.")
    return 1 if refused else 0


if __name__ == "__main__":
    raise SystemExit(main())
