"""Migrate valid Codex export directories from one root to another.

Finds ``lrh-codex-export-*`` directories under ``--source`` (default:
``${TMPDIR:-/tmp}``), validates each the same way ``find_exports.py`` does,
and copies the valid ones into ``--dest`` (default:
``~/.lrh/private/codex``, the durable location ``SKILL.md`` Step 2 already
documents as the alternative to ephemeral capture).

Copy-then-verify-then-delete-original, mirroring the sibling
``rescue_claude_sessions`` tooling's safety posture
(``migrate_memory.py``, ``archive_split_transcripts.py``): every copied file
is re-hashed against the source before the original directory is ever
removed. A name collision at the destination with *different* content is
refused, never silently overwritten or merged -- reconciling two exports
under the same directory name is a judgement call, not a mechanical one.

Every applied run appends an entry to ``<dest>/MIGRATION_LOG.md`` so the
destination stays self-documenting: what arrived, from where, and when.

Dry-run by default; pass --apply to write.
"""

from __future__ import annotations

import argparse
import shutil
import time
from pathlib import Path

import codexexportlib

MANIFEST_NAME = "MIGRATION_LOG.md"


def plan_move(
    candidates: list[codexexportlib.ExportCandidate], dest_root: Path
) -> tuple[list[Path], list[Path], list[Path]]:
    """Classify each valid candidate against the destination and each other.

    Returns ``(to_move, already_present, divergent)``, keyed by top-level
    candidate directory (not per-file, unlike ``migrate_memory.py``'s
    ``plan_copy`` -- an export directory is one unit here).

    Two candidates at different source depths can share a basename (the
    skill mints ``lrh-codex-export-<id>`` names independent of nesting
    depth). Checking only against the pre-run destination misses this: both
    would appear absent from ``dest_root`` during planning and both would be
    queued into ``to_move``, so the second ``shutil.copytree`` during
    ``--apply`` would collide with the first's freshly-written directory.
    Any such same-name collision within this candidate batch is refused the
    same way a source/destination content divergence is -- reconciling
    which one is authoritative is a judgement call, not a mechanical one.
    """
    to_move: list[Path] = []
    already_present: list[Path] = []
    divergent: list[Path] = []
    for candidate in candidates:
        if not candidate.valid:
            continue
        target = dest_root / candidate.path.name
        if not target.exists():
            to_move.append(candidate.path)
            continue
        source_files = sorted(p for p in candidate.path.rglob("*") if p.is_file())
        target_files = sorted(p for p in target.rglob("*") if p.is_file())
        source_rel = {p.relative_to(candidate.path) for p in source_files}
        target_rel = {p.relative_to(target) for p in target_files}
        if source_rel != target_rel:
            divergent.append(candidate.path)
            continue
        mismatched = any(
            codexexportlib.sha256_file(candidate.path / rel)
            != codexexportlib.sha256_file(target / rel)
            for rel in source_rel
        )
        if mismatched:
            divergent.append(candidate.path)
        else:
            already_present.append(candidate.path)

    by_name: dict[str, list[Path]] = {}
    for path in to_move:
        by_name.setdefault(path.name, []).append(path)
    colliding_names = {name for name, paths in by_name.items() if len(paths) > 1}
    if colliding_names:
        to_move = [p for p in to_move if p.name not in colliding_names]
        for name in colliding_names:
            divergent.extend(by_name[name])

    return to_move, already_present, divergent


def copy_and_verify(source_dir: Path, dest_dir: Path) -> list[str]:
    """Copy ``source_dir`` to ``dest_dir`` and re-hash every file.

    Returns a list of mismatch descriptions; empty means every file verified.
    Does not touch ``source_dir`` -- deletion is the caller's decision, made
    only once this returns empty.

    A ``copytree`` failure (permissions, ENOSPC, a source file vanishing
    mid-copy) is caught rather than left to crash the run: it can leave a
    partial ``dest_dir`` behind that would block a re-run's own "target
    already exists" check, so any partial copy is removed here before
    reporting the failure.
    """
    try:
        shutil.copytree(source_dir, dest_dir)
    except OSError as err:
        shutil.rmtree(dest_dir, ignore_errors=True)
        return [f"copy failed: {err}"]
    mismatched: list[str] = []
    for item in source_dir.rglob("*"):
        if not item.is_file():
            continue
        rel = item.relative_to(source_dir)
        target = dest_dir / rel
        if not target.exists():
            mismatched.append(f"missing at destination: {rel}")
        elif codexexportlib.sha256_file(item) != codexexportlib.sha256_file(target):
            mismatched.append(f"hash mismatch: {rel}")
    return mismatched


def _escape_table_cell(value: str) -> str:
    """Escape ``|`` so a path containing one cannot corrupt the Markdown table."""
    return value.replace("|", "\\|")


def append_manifest_entry(dest_root: Path, source_dir: Path, dest_dir: Path) -> None:
    """Append one row recording a single migrated directory's provenance.

    Called once per directory, immediately after that directory's copy is
    verified and *before* its original is deleted (see the call site in
    ``main``) -- not batched at the end of the run. Batching meant a
    manifest-write failure (an unwritable log, a full disk) could occur only
    after every source in the batch had already been deleted, leaving
    destination arrivals with no recoverable provenance. Writing and
    deleting one directory at a time makes each migration transactional: if
    this raises, the caller's ``source_dir`` is still on disk.
    """
    manifest = dest_root / MANIFEST_NAME
    is_new = not manifest.exists()
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with manifest.open("a", encoding="utf-8") as handle:
        if is_new:
            handle.write("# Codex export migration log\n\n")
            handle.write(
                "Appended by move_exports.py. Each row records one export "
                "directory's origin so nothing under this root loses its "
                "provenance.\n\n"
            )
            handle.write("| moved at (UTC) | source | dest |\n")
            handle.write("| --- | --- | --- |\n")
        source_cell = _escape_table_cell(str(source_dir))
        dest_cell = _escape_table_cell(str(dest_dir))
        handle.write(f"| {timestamp} | `{source_cell}` | `{dest_cell}` |\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="root to scan recursively (default: ${TMPDIR:-/tmp})",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=None,
        help=f"destination root (default: {codexexportlib.DEFAULT_DEST_ROOT})",
    )
    parser.add_argument(
        "--apply", action="store_true", help="actually move (default: dry run)"
    )
    args = parser.parse_args()

    source_root = (args.source or codexexportlib.default_source_root()).expanduser()
    dest_root = (args.dest or codexexportlib.DEFAULT_DEST_ROOT).expanduser()

    if codexexportlib.is_unsafe_pair(source_root, dest_root):
        print(f"REFUSE: --source ({source_root}) and --dest ({dest_root}) overlap")
        return 1

    if not source_root.is_dir():
        print(f"skip: not a directory: {source_root}")
        return 0

    dirs = codexexportlib.find_export_dirs(source_root)
    candidates = [codexexportlib.classify_export_dir(path) for path in dirs]
    invalid = [c for c in candidates if not c.valid]

    print(f"source: {source_root}")
    print(f"dest  : {dest_root}")
    print(
        f"found : {len(candidates)} candidate "
        f"{codexexportlib.pluralize_directories(len(candidates))}"
    )
    if invalid:
        print(f"skip  : {len(invalid)} invalid (not moved, see find_exports.py)")

    to_move, already_present, divergent = plan_move(candidates, dest_root)
    print(
        f"move  : {len(to_move)} {codexexportlib.pluralize_directories(len(to_move))}"
    )
    if already_present:
        print(
            f"same  : {len(already_present)} already present at destination, "
            "byte-identical"
        )

    if divergent:
        kind = codexexportlib.pluralize_directories(len(divergent))
        print(
            f"REFUSE: {len(divergent)} {kind} "
            "collide with different content at the destination:"
        )
        for path in divergent:
            print(f"        {path}  ->  {dest_root / path.name}")
        print("        reconcile these by hand, then re-run")
        return 1

    if not to_move:
        print("nothing to move")
        return 0

    if not args.apply:
        for path in to_move:
            print(f"  would move: {path}  ->  {dest_root / path.name}")
        print("(dry run - nothing written; pass --apply to move)")
        return 0

    dest_root.mkdir(parents=True, exist_ok=True)
    moved = 0
    failures = 0
    for source_dir in to_move:
        target = dest_root / source_dir.name
        mismatched = copy_and_verify(source_dir, target)
        if mismatched:
            print(f"  FAILED verification: {source_dir}")
            for line in mismatched[:10]:
                print(f"    {line}")
            print(f"    leaving original in place: {source_dir}")
            print(f"    removing unverified copy: {target}")
            shutil.rmtree(target, ignore_errors=True)
            failures += 1
            continue
        try:
            append_manifest_entry(dest_root, source_dir, target)
        except OSError as err:
            print(f"  FAILED to log provenance for {source_dir}: {err}")
            print(f"    leaving original in place: {source_dir}")
            print(f"    removing unlogged copy: {target}")
            shutil.rmtree(target, ignore_errors=True)
            failures += 1
            continue
        shutil.rmtree(source_dir)
        moved += 1
        print(f"  moved: {source_dir}  ->  {target}")

    if moved:
        kind = codexexportlib.pluralize_directories(moved)
        print(f"\n{moved} {kind} moved and verified")
        print(f"logged to {dest_root / MANIFEST_NAME}")
    if failures:
        print(f"{failures} failure(s) -- originals left in place, see above")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
