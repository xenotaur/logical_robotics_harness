"""Execution-record parsing and loading for LRH prompt workflows."""

from __future__ import annotations

import dataclasses
import pathlib
import typing

from lrh.control import parser as control_parser


@dataclasses.dataclass(frozen=True)
class ExecutionRecord:
    """Structured view of a prompt execution-record Markdown file."""

    path: pathlib.Path
    execution_id: str
    prompt_id: str
    work_item: str
    status: str
    rerun_of: str
    pr: str
    commit: str
    created_at: str
    frontmatter: dict[str, typing.Any]
    body: str


def parse_front_matter_fields(path: pathlib.Path) -> dict[str, str]:
    """Return string frontmatter fields from an execution record.

    Invalid or unreadable Markdown returns an empty mapping to preserve the
    historical prompt-check behavior of ignoring malformed records.
    """

    parsed = _parse_markdown_file_safely(path)
    if parsed is None:
        return {}

    fields: dict[str, str] = {}
    for key, value in parsed.frontmatter.items():
        if isinstance(value, str):
            fields[key] = value
    return fields


def parse_execution_record(path: pathlib.Path) -> ExecutionRecord | None:
    """Parse one execution-record Markdown file.

    Invalid or unreadable Markdown returns ``None`` so callers can load an
    execution tree without failing on unrelated draft or corrupt files.
    """

    parsed = _parse_markdown_file_safely(path)
    if parsed is None:
        return None

    return ExecutionRecord(
        path=path,
        execution_id=_frontmatter_string(parsed.frontmatter, "execution_id"),
        prompt_id=_frontmatter_string(parsed.frontmatter, "prompt_id"),
        work_item=_frontmatter_string(parsed.frontmatter, "work_item"),
        status=_frontmatter_string(parsed.frontmatter, "status"),
        rerun_of=_frontmatter_string(parsed.frontmatter, "rerun_of"),
        pr=_frontmatter_string(parsed.frontmatter, "pr"),
        commit=_frontmatter_string(parsed.frontmatter, "commit"),
        created_at=_frontmatter_string(parsed.frontmatter, "created_at"),
        frontmatter=dict(parsed.frontmatter),
        body=parsed.body,
    )


def load_execution_records(
    project_root: str | pathlib.Path,
    output_root: str | pathlib.Path = "project/executions",
) -> list[ExecutionRecord]:
    """Load execution records from ``output_root`` under ``project_root``."""

    execution_root = pathlib.Path(project_root) / output_root
    records: list[ExecutionRecord] = []
    for path in sorted(execution_root.glob("**/*.md")):
        record = parse_execution_record(path)
        if record is not None:
            records.append(record)
    return records


def _parse_markdown_file_safely(
    path: pathlib.Path,
) -> control_parser.ParsedMarkdown | None:
    try:
        return control_parser.parse_markdown_file(path)
    except (OSError, UnicodeDecodeError, ValueError):
        return None


def _frontmatter_string(frontmatter: dict[str, typing.Any], key: str) -> str:
    value = frontmatter.get(key, "")
    if isinstance(value, str):
        return value
    if value is None or isinstance(value, list):
        return ""
    return str(value)
