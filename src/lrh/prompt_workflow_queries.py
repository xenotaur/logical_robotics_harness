"""Execution-record query helpers for LRH prompt workflows."""

from __future__ import annotations

import dataclasses
import pathlib

from lrh import prompt_workflow_records


@dataclasses.dataclass(frozen=True)
class CheckExecutionResult:
    """Result of exact prompt-ID execution-record lookup."""

    prompt_id: str
    records: list[prompt_workflow_records.ExecutionRecord]

    @property
    def match_count(self) -> int:
        return len(self.records)

    @property
    def exit_code(self) -> int:
        if not self.records:
            return 1
        if len(self.records) > 1:
            return 2
        return 0


def check_execution(
    project_root: str | pathlib.Path,
    prompt_id: str,
    output_root: str | pathlib.Path = "project/executions",
) -> CheckExecutionResult:
    """Find execution records whose frontmatter prompt ID exactly matches."""

    records = prompt_workflow_records.load_execution_records(
        project_root=project_root,
        output_root=output_root,
    )
    matches = [record for record in records if record.prompt_id == prompt_id]
    return CheckExecutionResult(prompt_id=prompt_id, records=matches)
