"""Report path-keyed Claude Code state that a repository move left behind.

Read-only. Answers three questions:

1. Which projects now have two bucket spellings, and did ``memory/`` stay with
   the old one?
2. Which session ids exist in more than one bucket, and is the shorter copy a
   byte-exact prefix of the longer (safe to archive) or genuinely divergent?
3. Which not-yet-moved projects carry a memory corpus that *would* orphan if
   their repository moved next?
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import bucketlib


def build_report(aliases: list[tuple[Path, Path]]) -> dict:
    buckets = bucketlib.load_buckets()
    pairs = bucketlib.pair_buckets(buckets, aliases)
    # Only buckets whose counterpart actually exists are "handled"; the rest
    # still carry latent orphan risk for whenever their repository moves.
    paired_names = {old.name for old, _, new in pairs if new is not None}

    paired: list[dict] = []
    for old, expected, new in pairs:
        if new is None:
            continue
        paired.append(
            {
                "old_bucket": old.name,
                "new_bucket": new.name,
                "old_transcripts": len(old.transcripts()),
                "new_transcripts": len(new.transcripts()),
                "old_memory": old.memory_count(),
                "new_memory": new.memory_count(),
                "memory_orphaned": old.memory_count() > 0 and new.memory_count() <= 0,
            }
        )

    splits: list[dict] = []
    for session_id, paths in sorted(bucketlib.split_sessions(buckets).items()):
        ordered = sorted(paths, key=lambda p: p.stat().st_size, reverse=True)
        longest = ordered[0]
        copies = []
        for path in ordered:
            same_size = path.stat().st_size == longest.stat().st_size
            copies.append(
                {
                    "bucket": path.parent.name,
                    "bytes": path.stat().st_size,
                    "lines": bucketlib.count_lines(path),
                    "is_longest": path == longest,
                    "byte_prefix_of_longest": (
                        True if same_size and path == longest
                        else bucketlib.is_byte_prefix(path, longest)
                    ),
                }
            )
        splits.append(
            {
                "session_id": session_id,
                "copies": copies,
                "all_prefixes": all(c["byte_prefix_of_longest"] for c in copies),
            }
        )

    latent: list[dict] = []
    for name, bucket in buckets.items():
        if name in paired_names:
            continue
        is_old_root = any(
            name.startswith(bucketlib.slugify(old) + "-") for old, _ in aliases
        )
        if is_old_root and bucket.memory_count() > 0:
            latent.append(
                {
                    "bucket": name,
                    "memory": bucket.memory_count(),
                    "transcripts": len(bucket.transcripts()),
                }
            )

    truncated = [b.name for b in buckets.values() if b.truncated_slug()]

    return {
        "projects_root": str(bucketlib.projects_root()),
        "bucket_count": len(buckets),
        "paired": paired,
        "splits": splits,
        "latent_orphan_risk": sorted(latent, key=lambda r: -r["memory"]),
        "truncated_slugs": truncated,
    }


def print_report(report: dict) -> None:
    print(f"projects root : {report['projects_root']}")
    print(f"buckets       : {report['bucket_count']}")

    print("\n== paired buckets (both spellings on disk) ==")
    if not report["paired"]:
        print("  none")
    for row in report["paired"]:
        if row["memory_orphaned"]:
            status = "MEMORY ORPHANED"
        elif row["old_memory"] <= 0 and row["new_memory"] <= 0:
            status = "no memory corpus"
        else:
            status = "memory ok"
        show = lambda n: "-" if n < 0 else str(n)  # noqa: E731 - absent vs empty
        print(f"  {row['old_bucket']}")
        print(f"    -> {row['new_bucket']}")
        print(
            f"       transcripts {row['old_transcripts']} -> {row['new_transcripts']}"
            f"   memory {show(row['old_memory'])} -> {show(row['new_memory'])}   [{status}]"
        )

    print("\n== sessions split across buckets ==")
    if not report["splits"]:
        print("  none")
    for row in report["splits"]:
        verdict = "safe to archive shorter" if row["all_prefixes"] else "DIVERGENT - do not archive"
        print(f"  {row['session_id']}  [{verdict}]")
        for copy in row["copies"]:
            marker = "keep" if copy["is_longest"] else ("prefix" if copy["byte_prefix_of_longest"] else "DIVERGENT")
            print(
                f"    {copy['lines']:>7} lines  {copy['bytes']:>10} bytes  "
                f"{marker:<9} {copy['bucket']}"
            )

    print("\n== not yet moved, memory would orphan on next move ==")
    if not report["latent_orphan_risk"]:
        print("  none")
    for row in report["latent_orphan_risk"]:
        print(
            f"  {row['memory']:>4} memory files, {row['transcripts']:>3} transcripts  {row['bucket']}"
        )

    if report["truncated_slugs"]:
        print("\n== slugs at the 200-char truncation limit (pairing unreliable) ==")
        for name in report["truncated_slugs"]:
            print(f"  {name}")


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
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    raw = args.alias or list(bucketlib.DEFAULT_ALIASES)
    aliases = [bucketlib.parse_alias(item) for item in raw]

    report = build_report(aliases)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
