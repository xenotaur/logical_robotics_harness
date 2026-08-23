"""``lrh memory`` CLI: write, list, validate, repair, sync, read, search,
export, import, transfer.

PROP-LRH-MEMORY-COMMAND Stage 1 (WI-LRH-MEMORY-WRITE-SIDE), Stage 2
(WI-LRH-MEMORY-ARCHIVE-SIDE), Stage 3 (WI-LRH-MEMORY-READ-SIDE), and Stage 4
(WI-LRH-MEMORY-PORTABILITY). Thin CLI wiring over the core logic in
``prompt_workflow_memory``, following the same pattern as ``lrh sessions``
(``sessions_workflow.py`` over ``prompt_workflow_sessions``).
"""

from __future__ import annotations

import argparse
import json
import sys

from lrh import prompt_workflow_memory


def run_memory_cli(argv: list[str], *, prog: str = "lrh memory") -> int:
    parser = argparse.ArgumentParser(prog=prog, description="Memory corpus commands.")
    subparsers = parser.add_subparsers(dest="memory_command")

    write_parser = subparsers.add_parser(
        "write",
        help="Validate and write one memory file, plus its MEMORY.md entry.",
    )
    write_parser.add_argument("name", help="kebab-case memory name")
    write_parser.add_argument("--description", required=True)
    write_parser.add_argument(
        "--type", required=True, choices=prompt_workflow_memory.VALID_TYPES
    )
    write_parser.add_argument(
        "--agent", required=True, help="recorded as metadata.authored_by"
    )
    write_parser.add_argument(
        "--applies-to",
        default=None,
        help="comma-separated agents this memory applies to (default: --agent)",
    )
    write_parser.add_argument(
        "--body-file",
        default=None,
        help="path to the memory body; omit to read from stdin",
    )
    write_parser.add_argument("--project-root", default=".")
    write_parser.add_argument("--claude-projects-root", default=None)
    write_parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite even if authored_by differs from --agent",
    )

    list_parser = subparsers.add_parser("list", help="List the MEMORY.md index.")
    list_parser.add_argument("--project-root", default=".")
    list_parser.add_argument("--claude-projects-root", default=None)
    list_parser.add_argument("--agent", default=None)
    list_parser.add_argument("--format", choices=("text", "json"), default="text")

    validate_parser = subparsers.add_parser(
        "validate", help="Audit a memory corpus: malformed vs. legacy vs. conforming."
    )
    validate_parser.add_argument("--project-root", default=".")
    validate_parser.add_argument("--claude-projects-root", default=None)
    validate_parser.add_argument("--format", choices=("text", "json"), default="text")

    repair_parser = subparsers.add_parser(
        "repair",
        help="Conservative, structural-only fix-up of one memory's frontmatter.",
    )
    repair_parser.add_argument("name", help="kebab-case memory name")
    repair_parser.add_argument(
        "--set",
        dest="sets",
        action="append",
        default=[],
        metavar="FIELD=VALUE",
        help="repeatable; e.g. --set metadata.authored_by=claude",
    )
    repair_parser.add_argument("--project-root", default=".")
    repair_parser.add_argument("--claude-projects-root", default=None)
    repair_parser.add_argument("--dry-run", action="store_true")

    sync_parser = subparsers.add_parser(
        "sync",
        help=(
            "Mirror this project's memory corpus into the durable archive "
            "root, snapshotting any changed file's prior content first."
        ),
    )
    sync_parser.add_argument("--project-root", default=".")
    sync_parser.add_argument("--claude-projects-root", default=None)
    sync_parser.add_argument(
        "--archive-root",
        default=None,
        help=(
            "local archive root (default: $LRH_SESSION_ARCHIVE_ROOT, else "
            "~/.local/share/lrh/session-archive)"
        ),
    )
    sync_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would be mirrored without writing anything",
    )

    export_parser = subparsers.add_parser(
        "export",
        help="Export selected memories to a portable JSONL bundle.",
    )
    export_parser.add_argument("--output", required=True, help="bundle output path")
    export_parser.add_argument(
        "--name",
        dest="names",
        action="append",
        default=[],
        metavar="NAME",
        help="repeatable; kebab-case memory name to include",
    )
    export_parser.add_argument(
        "--agent", default=None, help="filter to memories authored_by this agent"
    )
    export_parser.add_argument("--project-root", default=".")
    export_parser.add_argument("--claude-projects-root", default=None)

    import_parser = subparsers.add_parser(
        "import",
        help=(
            "Import a portable JSONL bundle, writing each record through "
            "write's own validation."
        ),
    )
    import_parser.add_argument("--input", required=True, help="bundle input path")
    import_parser.add_argument(
        "--name",
        dest="names",
        action="append",
        default=[],
        metavar="NAME",
        help="repeatable; restrict import to these memory names",
    )
    import_parser.add_argument("--project-root", default=".")
    import_parser.add_argument("--claude-projects-root", default=None)
    import_parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "required to overwrite any existing destination memory -- "
            "same-agent, legacy (no authored_by), or a differing "
            "authored_by; the prior content is snapshotted first except "
            "for the differing-authored_by case"
        ),
    )
    import_parser.add_argument(
        "--dry-run", action="store_true", help="report what would be written"
    )

    transfer_parser = subparsers.add_parser(
        "transfer",
        help="Move memories between two corpora through a temp bundle (export+import).",
    )
    transfer_parser.add_argument(
        "--from",
        dest="from_",
        required=True,
        metavar="PATH-OR-SLUG",
        help="source project root path, or a literal project slug",
    )
    transfer_parser.add_argument(
        "--to",
        required=True,
        metavar="PATH-OR-SLUG",
        help="destination project root path, or a literal project slug",
    )
    transfer_parser.add_argument(
        "--name",
        dest="names",
        action="append",
        default=[],
        metavar="NAME",
        help="repeatable; kebab-case memory name to include",
    )
    transfer_parser.add_argument(
        "--agent", default=None, help="filter to memories authored_by this agent"
    )
    transfer_parser.add_argument("--claude-projects-root", default=None)
    transfer_parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "required to overwrite any existing destination memory -- "
            "same-agent, legacy (no authored_by), or a differing "
            "authored_by; the prior content is snapshotted first except "
            "for the differing-authored_by case"
        ),
    )
    transfer_parser.add_argument(
        "--dry-run", action="store_true", help="report what would be transferred"
    )

    read_parser = subparsers.add_parser(
        "read", help="Print one memory's full frontmatter and body."
    )
    read_parser.add_argument("name", help="kebab-case memory name")
    read_parser.add_argument("--project-root", default=".")
    read_parser.add_argument("--claude-projects-root", default=None)
    read_parser.add_argument("--format", choices=("text", "json"), default="text")

    search_parser = subparsers.add_parser(
        "search",
        help=(
            "Deterministic substring search over a memory corpus's "
            "frontmatter and body -- no semantic ranking."
        ),
    )
    search_parser.add_argument("query")
    search_parser.add_argument("--project-root", default=".")
    search_parser.add_argument("--claude-projects-root", default=None)
    search_parser.add_argument("--agent", default="")
    search_parser.add_argument(
        "--type",
        dest="type_",
        default="",
        choices=("",) + prompt_workflow_memory.VALID_TYPES,
    )
    search_parser.add_argument("--case-sensitive", action="store_true")
    search_parser.add_argument("--format", choices=("text", "json"), default="text")

    args = parser.parse_args(argv)
    if args.memory_command is None:
        parser.error("memory requires a subcommand (try: lrh memory list)")

    if args.memory_command == "write":
        return _run_write(args)
    if args.memory_command == "list":
        return _run_list(args)
    if args.memory_command == "validate":
        return _run_validate(args)
    if args.memory_command == "repair":
        return _run_repair(args)
    if args.memory_command == "sync":
        return _run_sync(args)
    if args.memory_command == "export":
        return _run_export(args)
    if args.memory_command == "import":
        return _run_import(args)
    if args.memory_command == "transfer":
        return _run_transfer(args)
    if args.memory_command == "read":
        return _run_read(args)
    if args.memory_command == "search":
        return _run_search(args)
    parser.error("memory requires a subcommand (try: lrh memory list)")
    return 2  # pragma: no cover -- parser.error raises SystemExit


def _run_write(args: argparse.Namespace) -> int:
    if args.body_file:
        with open(args.body_file, encoding="utf-8") as handle:
            body = handle.read()
    else:
        body = sys.stdin.read()

    applies_to = (
        [item.strip() for item in args.applies_to.split(",") if item.strip()]
        if args.applies_to
        else None
    )

    try:
        result = prompt_workflow_memory.write_memory(
            args.project_root,
            args.name,
            description=args.description,
            type_=args.type,
            agent=args.agent,
            applies_to=applies_to,
            body=body,
            claude_projects_root=args.claude_projects_root,
            force=args.force,
        )
    except prompt_workflow_memory.MemoryValidationError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(f"wrote: {result.memory_path}")
    if result.index_updated:
        print(f"indexed: {result.index_path}")
    else:
        print(f"index already current: {result.index_path}")
    return 0


def _run_list(args: argparse.Namespace) -> int:
    entries = prompt_workflow_memory.list_memories(
        args.project_root,
        claude_projects_root=args.claude_projects_root,
        agent=args.agent,
    )
    if args.format == "json":
        print(
            json.dumps(
                [
                    {
                        "filename": e.filename,
                        "line": e.line,
                        "authored_by": e.authored_by,
                    }
                    for e in entries
                ],
                indent=2,
            )
        )
        return 0
    if not entries:
        print("no memory index found for this project")
        return 0
    for entry in entries:
        print(entry.line)
    return 0


def _run_validate(args: argparse.Namespace) -> int:
    report = prompt_workflow_memory.validate_corpus(
        args.project_root, claude_projects_root=args.claude_projects_root
    )
    if args.format == "json":
        print(
            json.dumps(
                {
                    "malformed": list(report.malformed),
                    "unindexed": list(report.unindexed),
                    "legacy": list(report.legacy),
                    "conforming": list(report.conforming),
                },
                indent=2,
            )
        )
        return 0
    print(
        f"conforming: {len(report.conforming)}  "
        f"legacy: {len(report.legacy)}  "
        f"unindexed: {len(report.unindexed)}  "
        f"malformed: {len(report.malformed)}"
    )
    if report.unindexed:
        print(
            "unindexed (no MEMORY.md entry, unreachable by recall, repair candidates):"
        )
        for name in report.unindexed:
            print(f"  {name}")
    if report.legacy:
        print("legacy (missing authored_by, repair candidates):")
        for name in report.legacy:
            print(f"  {name}")
    if report.malformed:
        print("malformed (missing name/description/metadata.type):")
        for name in report.malformed:
            print(f"  {name}")
    return 0


def _run_repair(args: argparse.Namespace) -> int:
    sets: dict[str, str] = {}
    for item in args.sets:
        if "=" not in item:
            print(f"error: --set expects FIELD=VALUE, got {item!r}", file=sys.stderr)
            return 2
        key, value = item.split("=", 1)
        sets[key] = value

    try:
        path = prompt_workflow_memory.repair_memory(
            args.project_root,
            args.name,
            sets=sets,
            claude_projects_root=args.claude_projects_root,
            dry_run=args.dry_run,
        )
    except prompt_workflow_memory.MemoryValidationError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"would repair: {path}")
    else:
        print(f"repaired: {path}")
    return 0


def _run_sync(args: argparse.Namespace) -> int:
    entries = prompt_workflow_memory.sync_memory(
        args.project_root,
        claude_projects_root=args.claude_projects_root,
        archive_root=args.archive_root,
        dry_run=args.dry_run,
    )
    mirrored = 0
    unchanged = 0
    for entry in entries:
        if entry.copied:
            mirrored += 1
            verb = "would mirror" if args.dry_run else "mirrored"
            print(f"{verb}: {entry.source} -> {entry.dest}")
            if entry.snapshot is not None:
                print(f"  snapshot: {entry.snapshot}")
        else:
            unchanged += 1

    if args.dry_run:
        print(f"dry-run: {len(entries)} memory file(s) considered")
    else:
        print(f"sync complete: {mirrored} mirrored, {unchanged} unchanged")
    return 0


def _run_export(args: argparse.Namespace) -> int:
    try:
        result = prompt_workflow_memory.export_memories(
            args.project_root,
            output=args.output,
            names=args.names or None,
            agent=args.agent,
            claude_projects_root=args.claude_projects_root,
        )
    except (
        prompt_workflow_memory.MemoryValidationError,
        OSError,
        UnicodeDecodeError,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(f"exported: {result.count} memory(ies) -> {result.output_path}")
    return 0


def _report_import_entries(
    entries: list[prompt_workflow_memory.ImportEntry], *, dry_run: bool
) -> int:
    written = 0
    errors = 0
    for entry in entries:
        if entry.error is not None:
            errors += 1
            print(f"error: {entry.name}: {entry.error}", file=sys.stderr)
            continue
        if entry.written:
            written += 1
            print(f"wrote: {entry.name}")
        else:
            print(f"would write: {entry.name}")

    if dry_run:
        print(f"dry-run: {len(entries)} memory(ies) considered, {errors} would error")
    else:
        print(f"import complete: {written} written, {errors} errors")
    return 1 if errors else 0


def _run_import(args: argparse.Namespace) -> int:
    try:
        entries = prompt_workflow_memory.import_memories(
            args.project_root,
            input=args.input,
            names=args.names or None,
            force=args.force,
            dry_run=args.dry_run,
            claude_projects_root=args.claude_projects_root,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return _report_import_entries(entries, dry_run=args.dry_run)


def _run_transfer(args: argparse.Namespace) -> int:
    try:
        entries = prompt_workflow_memory.transfer_memories(
            from_=args.from_,
            to=args.to,
            names=args.names or None,
            agent=args.agent,
            force=args.force,
            dry_run=args.dry_run,
            claude_projects_root=args.claude_projects_root,
        )
    except (
        prompt_workflow_memory.MemoryValidationError,
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    return _report_import_entries(entries, dry_run=args.dry_run)


def _run_read(args: argparse.Namespace) -> int:
    try:
        result = prompt_workflow_memory.read_memory(
            args.project_root,
            args.name,
            claude_projects_root=args.claude_projects_root,
        )
    except (
        prompt_workflow_memory.MemoryValidationError,
        OSError,
        UnicodeDecodeError,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(
            json.dumps(
                {
                    "name": result.name,
                    "path": str(result.path),
                    "frontmatter": result.frontmatter,
                    "body": result.body,
                },
                indent=2,
                # yaml.safe_load parses YAML timestamps/dates into datetime
                # objects, which json.dumps cannot serialize by default --
                # a memory with such a value in its frontmatter would
                # otherwise crash `--format json` outright.
                default=str,
            )
        )
        return 0

    print(f"path: {result.path}")
    print(result.content, end="")
    return 0


def _run_search(args: argparse.Namespace) -> int:
    try:
        result = prompt_workflow_memory.search_memories(
            args.project_root,
            args.query,
            agent=args.agent,
            type_=args.type_,
            case_sensitive=args.case_sensitive,
            claude_projects_root=args.claude_projects_root,
        )
    except prompt_workflow_memory.MemoryValidationError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(
            json.dumps(
                {
                    "query": result.query,
                    "match_count": result.match_count,
                    "case_sensitive": result.case_sensitive,
                    "agent": result.agent,
                    "type": result.type_,
                    "mode": "exploratory_substring_search",
                    "memories": [
                        {
                            "name": match.name,
                            "path": str(match.path),
                            "authored_by": match.authored_by,
                            "contexts": match.contexts,
                        }
                        for match in result.matches
                    ],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return result.exit_code

    print(f"query: {result.query}")
    print(f"matches: {result.match_count}")
    filters = []
    if result.agent:
        filters.append(f"agent={result.agent}")
    if result.type_:
        filters.append(f"type={result.type_}")
    if filters:
        print(f"filters: {', '.join(filters)}")
    print("mode: deterministic substring search; no semantic ranking")
    if not result.matches:
        print("No memories matched.")
        return result.exit_code
    for match in result.matches:
        print(f"- {match.name} ({match.path})")
        if match.authored_by:
            print(f"  authored_by: {match.authored_by}")
        for context in match.contexts:
            print(f"  context: {context}")
    return result.exit_code
