"""Manual/dry-run run-report rendering for execution-ready work items."""

from __future__ import annotations

import dataclasses
import pathlib
from typing import Any

from lrh.control import execution_readiness
from lrh.control import parser as control_parser

_OUTCOMES = ("success", "blocked", "failed", "requires-human-review")
_REQUIRED_WORK_ITEM_FIELDS = ("id", "title", "type", "status")


@dataclasses.dataclass(frozen=True)
class ValidationResult:
    """One validation command result supplied by a human or dry-run caller."""

    command: str
    status: str
    evidence: str = ""


@dataclasses.dataclass(frozen=True)
class RunReportInput:
    """Structured input for a deterministic manual/dry-run run report."""

    work_item_path: pathlib.Path | str
    outcome: str
    run_packet_path: pathlib.Path | str | None = None
    validation_commands_intended: tuple[str, ...] = ()
    validation_commands_run: tuple[str, ...] = ()
    validation_results: tuple[ValidationResult, ...] = ()
    evidence_references: tuple[str, ...] = ()
    artifact_references: tuple[str, ...] = ()
    human_verification_tasks: tuple[str, ...] = ()
    policy_gate_states: tuple[str, ...] = ()
    human_gate_states: tuple[str, ...] = ()
    unresolved_risks: tuple[str, ...] = ()
    recommended_next_actions: tuple[str, ...] = ()
    prompt_execution_record: str = ""


@dataclasses.dataclass(frozen=True)
class RunReportDiagnostic:
    """Deterministic run-report diagnostic."""

    code: str
    message: str


@dataclasses.dataclass(frozen=True)
class RunReportResult:
    """Rendered run report and conservative diagnostics."""

    markdown: str
    diagnostics: tuple[RunReportDiagnostic, ...]


def outcome_choices() -> tuple[str, ...]:
    """Return supported report outcome states."""

    return _OUTCOMES


def render_run_report(
    report_input: RunReportInput,
    *,
    project_root: pathlib.Path | str | None = None,
) -> RunReportResult:
    """Render a non-mutating run report from explicit local inputs."""

    outcome = report_input.outcome.strip()
    if outcome not in _OUTCOMES:
        raise ValueError(
            "outcome must be one of: " + ", ".join(f"'{value}'" for value in _OUTCOMES)
        )

    work_item_path = pathlib.Path(report_input.work_item_path)
    parsed = control_parser.parse_markdown_file(work_item_path)
    readiness_issues = (
        *_validate_required_work_item_fields(work_item_path, parsed.frontmatter),
        *execution_readiness.validate_frontmatter(
            work_item_path,
            parsed.frontmatter,
            require_ready=True,
        ),
    )
    readiness = execution_readiness.from_frontmatter(parsed.frontmatter)
    diagnostics = _report_diagnostics(
        report_input=report_input,
        readiness=readiness,
        readiness_issues=readiness_issues,
    )

    markdown = _render_markdown(
        report_input=report_input,
        frontmatter=parsed.frontmatter,
        readiness=readiness,
        readiness_issues=readiness_issues,
        diagnostics=diagnostics,
        project_root=project_root,
        work_item_path=work_item_path,
    )
    return RunReportResult(markdown=markdown, diagnostics=diagnostics)


def parse_validation_result(text: str) -> ValidationResult:
    """Parse a CLI validation result as ``command :: status :: evidence``."""

    parts = [part.strip() for part in text.split("::", maxsplit=2)]
    if len(parts) < 2 or not parts[0] or not parts[1]:
        raise ValueError(
            "validation result must use 'command :: status' or "
            "'command :: status :: evidence'"
        )
    evidence = parts[2] if len(parts) == 3 else ""
    return ValidationResult(command=parts[0], status=parts[1], evidence=evidence)


def format_run_report_diagnostics(
    diagnostics: tuple[RunReportDiagnostic, ...],
) -> str:
    """Format report diagnostics as deterministic user-facing text."""

    if not diagnostics:
        return ""
    lines = ["warning: run report includes unresolved review diagnostics"]
    for diagnostic in diagnostics:
        lines.append(f"- {diagnostic.code}: {diagnostic.message}")
    return "\n".join(lines)


def _validate_required_work_item_fields(
    path: pathlib.Path,
    frontmatter: dict[str, Any],
) -> tuple[execution_readiness.ExecutionReadinessIssue, ...]:
    issues: list[execution_readiness.ExecutionReadinessIssue] = []
    for field in _REQUIRED_WORK_ITEM_FIELDS:
        value = frontmatter.get(field)
        if isinstance(value, str) and value.strip():
            continue
        issues.append(
            execution_readiness.ExecutionReadinessIssue(
                path=path,
                severity="error",
                code="WORK_ITEM_REQUIRED_FIELD_MISSING",
                message=f"missing required work-item field '{field}'",
            )
        )
    return tuple(issues)


def _report_diagnostics(
    *,
    report_input: RunReportInput,
    readiness: execution_readiness.ExecutionReadiness | None,
    readiness_issues: tuple[execution_readiness.ExecutionReadinessIssue, ...],
) -> tuple[RunReportDiagnostic, ...]:
    diagnostics: list[RunReportDiagnostic] = []
    for issue in readiness_issues:
        diagnostics.append(
            RunReportDiagnostic(
                code=issue.code,
                message=issue.message,
            )
        )

    intended = _intended_validation_commands(report_input, readiness)
    if (
        intended
        and not report_input.validation_commands_run
        and not report_input.validation_results
    ):
        diagnostics.append(
            RunReportDiagnostic(
                code="VALIDATION_RESULTS_MISSING",
                message=(
                    "intended validation commands are listed but no run "
                    "commands or results were supplied"
                ),
            )
        )
    if (
        readiness is not None
        and readiness.required_evidence
        and not report_input.evidence_references
    ):
        diagnostics.append(
            RunReportDiagnostic(
                code="EVIDENCE_REFERENCES_MISSING",
                message=(
                    "execution readiness requires evidence, but no evidence "
                    "references were supplied"
                ),
            )
        )
    if report_input.outcome == "success" and not report_input.evidence_references:
        diagnostics.append(
            RunReportDiagnostic(
                code="SUCCESS_EVIDENCE_MISSING",
                message=(
                    "success reports should include evidence references "
                    "before closeout"
                ),
            )
        )
    return tuple(sorted(diagnostics, key=lambda item: (item.code, item.message)))


def _render_markdown(
    *,
    report_input: RunReportInput,
    frontmatter: dict[str, Any],
    readiness: execution_readiness.ExecutionReadiness | None,
    readiness_issues: tuple[execution_readiness.ExecutionReadinessIssue, ...],
    diagnostics: tuple[RunReportDiagnostic, ...],
    project_root: pathlib.Path | str | None,
    work_item_path: pathlib.Path,
) -> str:
    work_item_id = _string_field(frontmatter, "id", default=work_item_path.stem)
    title = _string_field(frontmatter, "title", default="Untitled work item")
    status = _string_field(frontmatter, "status", default="unknown")
    source_path = _display_path(work_item_path, project_root)
    run_packet = _optional_path(report_input.run_packet_path, project_root)
    intended = _intended_validation_commands(report_input, readiness)
    artifacts = _artifact_references(report_input, readiness)

    lines = [
        f"# Run Report: {work_item_id}",
        "",
        (
            "> This report is a manual/dry-run diagnostic artifact. It records "
            "supplied outcomes, validation, evidence, and review tasks; it does "
            "not execute work, call agents, create branches, open pull requests, "
            "merge, release, publish, or replace prompt execution records."
        ),
        "",
        "## Generated Context",
        "",
        "- Generated by: `lrh request run-report-from-work-item`",
        (
            "- Determinism: no timestamp is embedded; callers should use the "
            "output path or surrounding record for chronology."
        ),
        (
            "- Relationship to prompt execution records: this run report "
            "describes one manual/dry-run execution attempt; `project/executions/` "
            "records continue to trace prompt-driven PR work."
        ),
        "",
        "## Linked Work Item",
        "",
        f"- ID: `{work_item_id}`",
        f"- Title: {title}",
        f"- Work-item status: `{status}`",
        f"- Source path: `{source_path}`",
        "",
        "## Linked Run Packet",
        "",
        f"- Run packet: {_inline_code_or_none(run_packet)}",
        "",
        "## Execution Readiness Summary",
        "",
    ]
    lines.extend(_readiness_summary(readiness, readiness_issues))
    lines.extend(
        [
            "",
            "## Outcome Status",
            "",
            f"- Reported outcome: `{report_input.outcome}`",
            (
                "- Conservative interpretation: "
                f"{_outcome_interpretation(report_input.outcome, diagnostics)}"
            ),
            "",
            "## Validation Commands Intended",
            "",
        ]
    )
    lines.extend(_list_lines(intended, code=True))
    lines.extend(["", "## Validation Commands Actually Run", ""])
    lines.extend(_list_lines(report_input.validation_commands_run, code=True))
    lines.extend(["", "## Validation Results", ""])
    lines.extend(_validation_result_lines(report_input.validation_results))
    lines.extend(["", "## Evidence References", ""])
    lines.extend(_list_lines(report_input.evidence_references))
    lines.extend(["", "## Generated or Expected Artifact References", ""])
    lines.extend(_list_lines(artifacts))
    lines.extend(["", "## Human Verification Tasks", ""])
    lines.extend(_list_lines(report_input.human_verification_tasks))
    lines.extend(["", "## Policy-Gate State", ""])
    lines.extend(_list_lines(_policy_gate_states(report_input, readiness)))
    lines.extend(["", "## Human-Gate State", ""])
    lines.extend(_list_lines(_human_gate_states(report_input, readiness)))
    lines.extend(["", "## Unresolved Risks or Missing Evidence", ""])
    lines.extend(_risk_lines(report_input.unresolved_risks, diagnostics))
    lines.extend(["", "## Recommended Next Actions", ""])
    lines.extend(_list_lines(report_input.recommended_next_actions))
    lines.extend(["", "## Prompt Execution Record Relationship", ""])
    lines.extend(_prompt_record_lines(report_input.prompt_execution_record))
    return "\n".join(lines).rstrip() + "\n"


def _readiness_summary(
    readiness: execution_readiness.ExecutionReadiness | None,
    readiness_issues: tuple[execution_readiness.ExecutionReadinessIssue, ...],
) -> list[str]:
    if readiness is None:
        return ["- Execution readiness: not available or not opted in."]
    lines = [
        f"- Execution ready: {_yes_no(readiness.execution_ready)}",
        f"- Autonomy level: `{readiness.autonomy_level}`",
        f"- Operation risk: `{readiness.operation_risk}`",
        f"- Required evidence declared: {_format_values(readiness.required_evidence)}",
        (
            "- Expected artifacts declared: "
            f"{_format_values(readiness.expected_artifacts)}"
        ),
    ]
    if not readiness_issues:
        lines.append(
            "- Readiness diagnostics: none from strict selected-leaf validation."
        )
    else:
        lines.append("- Readiness diagnostics:")
        for issue in readiness_issues:
            lines.append(f"  - `{issue.code}`: {issue.message}")
    return lines


def _outcome_interpretation(
    outcome: str,
    diagnostics: tuple[RunReportDiagnostic, ...],
) -> str:
    if diagnostics:
        return (
            "human review required before treating the reported outcome as "
            "closeout evidence"
        )
    interpretations = {
        "success": (
            "supplied evidence and validation may support closeout after human "
            "review"
        ),
        "blocked": "work is blocked; resolve blockers before another attempt",
        "failed": "attempt failed; inspect validation/evidence before retrying",
        "requires-human-review": (
            "human review is required before closeout or follow-up execution"
        ),
    }
    return interpretations[outcome]


def _validation_result_lines(results: tuple[ValidationResult, ...]) -> list[str]:
    if not results:
        return ["- None supplied."]
    lines: list[str] = []
    for result in results:
        evidence = f"; evidence: {result.evidence}" if result.evidence else ""
        lines.append(f"- `{result.command}`: {result.status}{evidence}")
    return lines


def _risk_lines(
    risks: tuple[str, ...],
    diagnostics: tuple[RunReportDiagnostic, ...],
) -> list[str]:
    lines: list[str] = []
    for risk in risks:
        lines.append(f"- {risk}")
    for diagnostic in diagnostics:
        lines.append(f"- `{diagnostic.code}`: {diagnostic.message}")
    return lines or ["- None supplied."]


def _prompt_record_lines(prompt_execution_record: str) -> list[str]:
    if not prompt_execution_record.strip():
        return [
            "- Prompt execution record: none supplied.",
            (
                "- Run reports do not replace `project/executions/` records "
                "for prompt-driven PR traceability."
            ),
        ]
    return [
        f"- Prompt execution record: `{prompt_execution_record.strip()}`",
        (
            "- Run reports describe execution attempts; execution records "
            "describe prompt-driven PR work."
        ),
    ]


def _policy_gate_states(
    report_input: RunReportInput,
    readiness: execution_readiness.ExecutionReadiness | None,
) -> tuple[str, ...]:
    if report_input.policy_gate_states:
        return report_input.policy_gate_states
    if readiness is None or not readiness.policy_gates:
        return ()
    return tuple(f"{gate}: not reported" for gate in readiness.policy_gates)


def _human_gate_states(
    report_input: RunReportInput,
    readiness: execution_readiness.ExecutionReadiness | None,
) -> tuple[str, ...]:
    if report_input.human_gate_states:
        return report_input.human_gate_states
    if readiness is None:
        return ()
    approval = (
        "required" if readiness.requires_human_approval else "not declared required"
    )
    merge = "required" if readiness.requires_human_merge else "not declared required"
    closeout = (
        "required" if readiness.requires_human_closeout else "not declared required"
    )
    return (
        f"human approval before execution: {approval}",
        f"human merge: {merge}",
        f"human closeout: {closeout}",
    )


def _intended_validation_commands(
    report_input: RunReportInput,
    readiness: execution_readiness.ExecutionReadiness | None,
) -> tuple[str, ...]:
    if report_input.validation_commands_intended:
        return report_input.validation_commands_intended
    if readiness is None:
        return ()
    return readiness.validation_commands


def _artifact_references(
    report_input: RunReportInput,
    readiness: execution_readiness.ExecutionReadiness | None,
) -> tuple[str, ...]:
    values: list[str] = []
    values.extend(report_input.artifact_references)
    if readiness is not None:
        for artifact in readiness.expected_artifacts:
            if artifact not in values:
                values.append(artifact)
    return tuple(values)


def _list_lines(values: tuple[str, ...], *, code: bool = False) -> list[str]:
    if not values:
        return ["- None supplied."]
    if code:
        return [f"- `{value}`" for value in values]
    return [f"- {value}" for value in values]


def _format_values(values: tuple[str, ...]) -> str:
    if not values:
        return "none"
    return ", ".join(f"`{value}`" for value in values)


def _string_field(frontmatter: dict[str, Any], field: str, *, default: str) -> str:
    value = frontmatter.get(field)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def _optional_path(
    value: pathlib.Path | str | None,
    project_root: pathlib.Path | str | None,
) -> str:
    if value is None or str(value).strip() == "":
        return ""
    return _display_path(pathlib.Path(value), project_root)


def _display_path(path: pathlib.Path, project_root: pathlib.Path | str | None) -> str:
    if project_root is None:
        return path.as_posix()
    root = pathlib.Path(project_root)
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _inline_code_or_none(value: str) -> str:
    if not value:
        return "none supplied"
    return f"`{value}`"


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"
