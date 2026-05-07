"""Prompt-file matching helpers for LRH prompt workflows."""

from __future__ import annotations

import argparse
import dataclasses
import pathlib
import re
import sys

from lrh import prompt_workflow_queries, prompt_workflow_records

PROMPT_ID_PATTERN = re.compile(
    r"PROMPT\("
    r"[A-Za-z0-9][A-Za-z0-9_-]*"
    r":"
    r"[A-Z0-9][A-Z0-9_]*"
    r"\)\["
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?"
    r"(?:Z|[+-]\d{2}:\d{2})"
    r"\]"
)


@dataclasses.dataclass(frozen=True)
class PromptExecutionMatchResult:
    """Exact execution-record lookup result for one prompt ID."""

    prompt_id: str
    check_result: prompt_workflow_queries.CheckExecutionResult

    @property
    def match_count(self) -> int:
        return self.check_result.match_count


@dataclasses.dataclass(frozen=True)
class PromptFileExecutionMatchResult:
    """Exact prompt-file-to-execution matching result."""

    prompt_file: pathlib.Path
    matches: list[PromptExecutionMatchResult]

    @property
    def prompt_ids(self) -> list[str]:
        return [match.prompt_id for match in self.matches]

    @property
    def exit_code(self) -> int:
        if not self.matches:
            return 1
        if any(match.match_count > 1 for match in self.matches):
            return 2
        if any(match.match_count == 0 for match in self.matches):
            return 1
        return 0


def extract_prompt_ids(text: str) -> list[str]:
    """Extract full prompt IDs in source order, de-duplicating repeats."""

    prompt_ids: list[str] = []
    seen: set[str] = set()
    for match in PROMPT_ID_PATTERN.finditer(text):
        prompt_id = match.group(0)
        if prompt_id not in seen:
            prompt_ids.append(prompt_id)
            seen.add(prompt_id)
    return prompt_ids


def match_prompt_file_to_executions(
    prompt_file: str | pathlib.Path,
    *,
    project_root: str | pathlib.Path,
    output_root: str | pathlib.Path = "project/executions",
) -> PromptFileExecutionMatchResult:
    """Match prompt IDs in a UTF-8 prompt file to execution records exactly."""

    prompt_path = pathlib.Path(prompt_file)
    text = prompt_path.read_text(encoding="utf-8")
    prompt_ids = extract_prompt_ids(text)
    if not prompt_ids:
        return PromptFileExecutionMatchResult(prompt_file=prompt_path, matches=[])

    records = prompt_workflow_records.load_execution_records(
        project_root=project_root,
        output_root=output_root,
    )
    matches: list[PromptExecutionMatchResult] = []
    for prompt_id in prompt_ids:
        check_result = prompt_workflow_queries.check_execution_records(
            records=records,
            prompt_id=prompt_id,
        )
        matches.append(
            PromptExecutionMatchResult(
                prompt_id=prompt_id,
                check_result=check_result,
            )
        )
    return PromptFileExecutionMatchResult(prompt_file=prompt_path, matches=matches)


def format_text_result(result: PromptFileExecutionMatchResult) -> str:
    """Render human-readable exact prompt-file matching results."""

    lines = [f"prompt_file: {result.prompt_file.as_posix()}"]
    if not result.matches:
        lines.append("No prompt IDs found in prompt file.")
        return "\n".join(lines) + "\n"

    for match in result.matches:
        lines.append(f"prompt_id: {match.prompt_id}")
        if match.match_count == 0:
            lines.append("  exact: no execution records found")
            continue
        if match.match_count == 1:
            lines.append("  exact: 1 execution record found")
        else:
            lines.append(
                "  exact: multiple execution records found; human review required"
            )
        for record in match.check_result.records:
            lines.append(
                "  - "
                f"{record.path.as_posix()}"
                f"\tstatus={record.status}"
                f"\twork_item={record.work_item}"
            )
    return "\n".join(lines) + "\n"


def run_match_cli(argv: list[str], *, prog: str = "lrh match") -> int:
    """Run installed prompt matching CLI commands."""

    parser = argparse.ArgumentParser(
        prog=prog,
        description="Match prompt files to execution records.",
    )
    subparsers = parser.add_subparsers(dest="match_command")
    executions_parser = subparsers.add_parser(
        "executions",
        help="Match prompt IDs in a prompt file to execution records exactly.",
    )
    executions_parser.add_argument("prompt_file")
    executions_parser.add_argument("--project-root", default=".")
    executions_parser.add_argument("--output-root", default="project/executions")

    args = parser.parse_args(argv)
    if args.match_command is None:
        parser.error("match requires a subcommand (try: lrh match executions)")

    try:
        result = match_prompt_file_to_executions(
            args.prompt_file,
            project_root=args.project_root,
            output_root=args.output_root,
        )
    except (OSError, UnicodeDecodeError) as error:
        print(f"error: unable to read prompt file: {error}", file=sys.stderr)
        return 2

    print(format_text_result(result), end="")
    return result.exit_code
