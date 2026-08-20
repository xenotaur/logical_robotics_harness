"""``lrh memory`` CLI: write, list, validate, repair.

PROP-LRH-MEMORY-COMMAND Stage 1 (WI-LRH-MEMORY-WRITE-SIDE). Thin CLI wiring
over the core logic in ``prompt_workflow_memory``, following the same
pattern as ``lrh sessions`` (``sessions_workflow.py`` over
``prompt_workflow_sessions``).

Does not implement ``sync`` (WI-LRH-MEMORY-ARCHIVE-SIDE), ``read``/``search``
(WI-LRH-MEMORY-READ-SIDE), or ``export``/``import``/``transfer``
(WI-LRH-MEMORY-PORTABILITY).
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
    parser.error("memory requires a subcommand (try: lrh memory list)")
    return 2  # pragma: no cover -- parser.error raises SystemExit


def _run_write(args: argparse.Namespace) -> int:
    if args.body_file:
        body = open(args.body_file, encoding="utf-8").read()
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
        f"malformed: {len(report.malformed)}"
    )
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
