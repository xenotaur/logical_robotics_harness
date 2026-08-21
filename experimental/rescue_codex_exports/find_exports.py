"""Find Codex export directories under a root and report their validity.

Read-only. Recursively scans ``--source`` (default: ``${TMPDIR:-/tmp}``, the
skill's own ephemeral default -- see SKILL.md Step 2) for directories
matching the ``lrh-codex-export-*`` name pattern, and classifies each as
valid, missing a required file, or empty. Prints a report; writes nothing.

Also usable against a non-default root, such as a personal export archive
directory, to audit what is actually sitting there before running
``move_exports.py`` against it.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import codexexportlib


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="root to scan recursively (default: ${TMPDIR:-/tmp})",
    )
    args = parser.parse_args()

    source = (args.source or codexexportlib.default_source_root()).expanduser()
    print(f"scanning: {source}")

    if not source.is_dir():
        print(f"  skip: not a directory: {source}")
        return 1

    dirs = codexexportlib.find_export_dirs(source)
    if not dirs:
        print("  no lrh-codex-export-* directories found")
        return 0

    candidates = [codexexportlib.classify_export_dir(path) for path in dirs]
    by_status: dict[str, list[codexexportlib.ExportCandidate]] = {}
    for candidate in candidates:
        by_status.setdefault(candidate.status, []).append(candidate)

    valid = by_status.get("valid", [])
    kind = codexexportlib.pluralize_directories(len(candidates))
    print(f"  found: {len(candidates)} candidate {kind}")
    print(f"  valid: {len(valid)}")
    for candidate in valid:
        print(f"    {candidate.path}")

    for status in ("missing_export_md", "missing_raw_json", "empty"):
        problems = by_status.get(status, [])
        if not problems:
            continue
        print(f"  {status}: {len(problems)}")
        for candidate in problems:
            print(f"    {candidate.path}  ({'; '.join(candidate.issues)})")

    print(f"\n{len(valid)} valid, {len(candidates) - len(valid)} skipped as invalid")
    if valid:
        print("Run move_exports.py (dry-run by default) to migrate the valid ones.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
