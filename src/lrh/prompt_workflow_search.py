"""Exploratory execution-record search helpers for LRH prompt workflows."""

from __future__ import annotations

import argparse
import dataclasses
import json
import pathlib
import sys
import typing

from lrh import prompt_workflow, prompt_workflow_records

VALID_EXECUTION_STATUSES = tuple(sorted(prompt_workflow.VALID_STATUSES))


@dataclasses.dataclass(frozen=True)
class ExecutionSearchMatch:
    """One execution record matched by exploratory text search."""

    record: prompt_workflow_records.ExecutionRecord
    contexts: list[str]


@dataclasses.dataclass(frozen=True)
class ExecutionSearchResult:
    """Exploratory execution-record text search result."""

    query: str
    matches: list[ExecutionSearchMatch]
    case_sensitive: bool
    status: str = ""
    work_item: str = ""

    @property
    def match_count(self) -> int:
        return len(self.matches)

    @property
    def exit_code(self) -> int:
        if self.matches:
            return 0
        return 1


def search_execution_records(
    records: list[prompt_workflow_records.ExecutionRecord],
    query: str,
    *,
    status: str = "",
    work_item: str = "",
    case_sensitive: bool = False,
) -> ExecutionSearchResult:
    """Search loaded execution records by deterministic substring matching.

    This helper is exploratory: it searches selected frontmatter text and body
    text, and it is not a substitute for exact prompt ID checks used for prompt
    soft idempotence decisions.
    """

    if query == "":
        raise ValueError("query must not be empty")

    matches: list[ExecutionSearchMatch] = []
    comparable_query = _comparable(query, case_sensitive=case_sensitive)
    for record in sorted(records, key=lambda item: item.path.as_posix()):
        if status and record.status != status:
            continue
        if work_item and record.work_item != work_item:
            continue

        contexts = _matching_contexts(
            record,
            comparable_query,
            case_sensitive=case_sensitive,
        )
        if contexts:
            matches.append(ExecutionSearchMatch(record=record, contexts=contexts))

    return ExecutionSearchResult(
        query=query,
        matches=matches,
        case_sensitive=case_sensitive,
        status=status,
        work_item=work_item,
    )


def search_executions(
    project_root: str | pathlib.Path,
    query: str,
    *,
    output_root: str | pathlib.Path = "project/executions",
    status: str = "",
    work_item: str = "",
    case_sensitive: bool = False,
) -> ExecutionSearchResult:
    """Load execution records and run exploratory text search."""

    records = prompt_workflow_records.load_execution_records(
        project_root=project_root,
        output_root=output_root,
    )
    return search_execution_records(
        records,
        query,
        status=status,
        work_item=work_item,
        case_sensitive=case_sensitive,
    )


def format_text_result(result: ExecutionSearchResult) -> str:
    """Render human-readable exploratory search results."""

    lines = [f"query: {result.query}", f"matches: {result.match_count}"]
    filters = _format_filters(result)
    if filters:
        lines.append(f"filters: {filters}")
    lines.append(
        "mode: exploratory substring search; "
        "not authoritative for soft idempotence decisions"
    )

    if not result.matches:
        lines.append("No execution records matched.")
        return "\n".join(lines) + "\n"

    for match in result.matches:
        record = match.record
        lines.append(f"- {record.path.as_posix()}")
        lines.append(f"  status: {record.status}")
        lines.append(f"  work_item: {record.work_item}")
        if record.prompt_id:
            lines.append(f"  prompt_id: {record.prompt_id}")
        for context in match.contexts:
            lines.append(f"  context: {context}")
    return "\n".join(lines) + "\n"


def format_json_result(result: ExecutionSearchResult) -> str:
    """Render deterministic JSON search results."""

    payload = {
        "query": result.query,
        "match_count": result.match_count,
        "case_sensitive": result.case_sensitive,
        "status": result.status,
        "work_item": result.work_item,
        "mode": "exploratory_substring_search",
        "authoritative_for_idempotence": False,
        "records": [
            {
                "path": match.record.path.as_posix(),
                "execution_id": match.record.execution_id,
                "prompt_id": match.record.prompt_id,
                "work_item": match.record.work_item,
                "status": match.record.status,
                "contexts": match.contexts,
            }
            for match in result.matches
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def run_search_cli(argv: list[str], *, prog: str = "lrh search") -> int:
    """Run installed exploratory search CLI commands."""

    parser = argparse.ArgumentParser(
        prog=prog,
        description="Search local LRH project records.",
    )
    subparsers = parser.add_subparsers(dest="search_command")
    executions_parser = subparsers.add_parser(
        "executions",
        help="Exploratory substring search over execution records.",
        description=(
            "Search execution-record frontmatter and body text locally. "
            "Results are exploratory and are not authoritative for "
            "soft idempotence decisions; use `lrh prompt check-execution` "
            "for exact prompt ID lookup."
        ),
    )
    executions_parser.add_argument("query")
    executions_parser.add_argument("--project-root", default=".")
    executions_parser.add_argument("--output-root", default="project/executions")
    executions_parser.add_argument("--status", choices=VALID_EXECUTION_STATUSES)
    executions_parser.add_argument("--work-item", default="")
    executions_parser.add_argument("--case-sensitive", action="store_true")
    executions_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format (default: text)",
    )

    args = parser.parse_args(argv)
    if args.search_command is None:
        parser.error("search requires a subcommand (try: lrh search executions)")

    try:
        result = search_executions(
            project_root=args.project_root,
            output_root=args.output_root,
            query=args.query,
            status=args.status or "",
            work_item=args.work_item,
            case_sensitive=args.case_sensitive,
        )
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(format_json_result(result), end="")
    else:
        print(format_text_result(result), end="")
    return result.exit_code


def _matching_contexts(
    record: prompt_workflow_records.ExecutionRecord,
    comparable_query: str,
    *,
    case_sensitive: bool,
) -> list[str]:
    contexts: list[str] = []
    for label, text in _searchable_segments(record):
        comparable_text = _comparable(text, case_sensitive=case_sensitive)
        if comparable_query in comparable_text:
            contexts.append(f"{label}: {_compact_context(text)}")
        if len(contexts) >= 3:
            break
    return contexts


def _searchable_segments(
    record: prompt_workflow_records.ExecutionRecord,
) -> list[tuple[str, str]]:
    segments: list[tuple[str, str]] = []
    for key in sorted(record.frontmatter):
        segments.append((f"frontmatter.{key}", _stringify(record.frontmatter[key])))
    for line_number, line in enumerate(record.body.splitlines(), start=1):
        if line.strip():
            segments.append((f"body:{line_number}", line.strip()))
    return segments


def _stringify(value: typing.Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    if value is None:
        return ""
    return str(value)


def _comparable(value: str, *, case_sensitive: bool) -> str:
    if case_sensitive:
        return value
    return value.casefold()


def _compact_context(value: str) -> str:
    compacted = " ".join(value.split())
    if len(compacted) <= 160:
        return compacted
    return compacted[:157].rstrip() + "..."


def _format_filters(result: ExecutionSearchResult) -> str:
    filters: list[str] = []
    if result.status:
        filters.append(f"status={result.status}")
    if result.work_item:
        filters.append(f"work_item={result.work_item}")
    if result.case_sensitive:
        filters.append("case_sensitive=true")
    return ", ".join(filters)
