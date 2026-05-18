"""Dry-run run-packet rendering for execution-ready work items."""

from __future__ import annotations

import dataclasses
import pathlib
import re
from typing import Any

from lrh.control import execution_readiness
from lrh.control import parser as control_parser

_SECTION_HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
_REQUIRED_WORK_ITEM_FIELDS = ("id", "title", "type", "status")


@dataclasses.dataclass(frozen=True)
class RunPacketResult:
    """Rendered dry-run packet and source diagnostics."""

    markdown: str
    diagnostics: tuple[execution_readiness.ExecutionReadinessIssue, ...]


def render_run_packet_from_work_item(
    work_item_path: pathlib.Path | str,
    *,
    project_root: pathlib.Path | str | None = None,
) -> RunPacketResult:
    """Render a non-mutating dry-run run packet for one execution-ready work item."""

    path = pathlib.Path(work_item_path)
    parsed = control_parser.parse_markdown_file(path)
    diagnostics = (
        *_validate_required_work_item_fields(path, parsed.frontmatter),
        *execution_readiness.validate_frontmatter(
            path,
            parsed.frontmatter,
            require_ready=True,
        ),
    )
    if diagnostics:
        return RunPacketResult(
            markdown=_render_diagnostic_packet(
                path=path,
                frontmatter=parsed.frontmatter,
                diagnostics=diagnostics,
                project_root=project_root,
            ),
            diagnostics=diagnostics,
        )

    readiness = execution_readiness.from_frontmatter(parsed.frontmatter)
    if readiness is None:
        raise ValueError(
            "internal error: readiness validation passed without readiness"
        )

    return RunPacketResult(
        markdown=_render_ready_packet(
            path=path,
            frontmatter=parsed.frontmatter,
            body=parsed.body,
            readiness=readiness,
            project_root=project_root,
        ),
        diagnostics=(),
    )


def format_readiness_diagnostics(
    diagnostics: tuple[execution_readiness.ExecutionReadinessIssue, ...],
) -> str:
    """Format readiness diagnostics as deterministic user-facing text."""

    if not diagnostics:
        return ""
    lines = ["error: work item is not execution-ready for run-packet generation"]
    for issue in diagnostics:
        lines.append(f"- {issue.code}: {issue.message} ({issue.path})")
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


def _render_ready_packet(
    *,
    path: pathlib.Path,
    frontmatter: dict[str, Any],
    body: str,
    readiness: execution_readiness.ExecutionReadiness,
    project_root: pathlib.Path | str | None,
) -> str:
    sections = _extract_sections(body)
    title = _string_field(frontmatter, "title", default="Untitled work item")
    work_item_id = _string_field(frontmatter, "id", default=path.stem)
    status = _string_field(frontmatter, "status", default="unknown")
    source_path = _display_path(path, project_root)

    lines = [
        f"# Dry-Run Run Packet: {work_item_id}",
        "",
        "> This packet is a dry-run/manual artifact. It does not invoke agents, "
        "create branches, open pull requests, merge, release, publish, or mutate "
        "repository state except when a human explicitly writes this packet to the "
        "requested output path.",
        "",
        "## Work Item",
        "",
        f"- ID: `{work_item_id}`",
        f"- Title: {title}",
        f"- Status: `{status}`",
        f"- Source path: `{source_path}`",
        "",
        "## Related Planning References",
        "",
    ]
    lines.extend(
        _bullet_values("Workstreams", _list_field(frontmatter, "related_workstreams"))
    )
    lines.extend(_bullet_values("Focus", _list_field(frontmatter, "related_focus")))
    lines.extend(_bullet_values("Roadmap", _list_field(frontmatter, "related_roadmap")))
    lines.extend(_bullet_values("Design", _list_field(frontmatter, "related_design")))
    lines.extend(_bullet_values("Depends on", _list_field(frontmatter, "depends_on")))
    lines.extend(
        [
            "",
            "## Task Summary",
            "",
            _section_or_fallback(
                sections, ("summary", "problem / context"), "No task summary provided."
            ),
            "",
            "## Required Changes",
            "",
            _section_or_fallback(
                sections, ("required changes",), "No required changes section provided."
            ),
            "",
            "## Explicit Scope",
            "",
            _section_or_fallback(
                sections, ("scope",), "No explicit scope section provided."
            ),
            "",
            "## Allowed Paths",
            "",
        ]
    )
    lines.extend(_list_lines(readiness.allowed_paths))
    lines.extend(["", "## Forbidden Paths", ""])
    lines.extend(_list_lines(readiness.forbidden_paths))
    lines.extend(["", "## Forbidden Actions", ""])
    lines.extend(_list_lines(_forbidden_actions(frontmatter)))
    lines.extend(["", "## Validation Commands", ""])
    lines.extend(_list_lines(readiness.validation_commands, code=True))
    lines.extend(["", "## Expected Evidence and Artifacts", ""])
    lines.extend(_labeled_list("Required evidence", readiness.required_evidence))
    lines.extend(
        _labeled_list("Expected artifacts", _expected_artifacts(frontmatter, readiness))
    )
    lines.extend(["", "## Human Gates", ""])
    lines.extend(
        [
            "- Human approval required before execution: "
            f"{_yes_no(readiness.requires_human_approval)}",
            f"- Human merge required: {_yes_no(readiness.requires_human_merge)}",
            f"- Human closeout required: {_yes_no(readiness.requires_human_closeout)}",
        ]
    )
    lines.extend(["", "## Autonomy and Risk", ""])
    lines.extend(
        [
            f"- Autonomy level: `{readiness.autonomy_level}`",
            f"- Operation risk: `{readiness.operation_risk}`",
            f"- Max review rounds: {_optional_int(readiness.max_review_rounds)}",
            f"- Max CI rounds: {_optional_int(readiness.max_ci_rounds)}",
        ]
    )
    lines.extend(_labeled_list("Policy gates", readiness.policy_gates))
    lines.extend(_labeled_list("Agent constraints", readiness.agent_constraints))
    lines.extend(
        [
            "",
            "## Missing Readiness Fields / Review Tasks",
            "",
            "- None. The selected work item passed strict "
            "execution-readiness checks for packet generation.",
            "",
            "## Manual Closeout Reminder",
            "",
            "- Review this packet before handing it to any human or "
            "assistant workflow.",
            "- Record evidence from validation commands, logs, screenshots, "
            "reports, or review notes before closeout.",
            "- Treat future runner dry-run semantics as separate from this "
            "request artifact unless a later contract explicitly aligns them.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _render_diagnostic_packet(
    *,
    path: pathlib.Path,
    frontmatter: dict[str, Any],
    diagnostics: tuple[execution_readiness.ExecutionReadinessIssue, ...],
    project_root: pathlib.Path | str | None,
) -> str:
    work_item_id = _string_field(frontmatter, "id", default=path.stem)
    title = _string_field(frontmatter, "title", default="Untitled work item")
    status = _string_field(frontmatter, "status", default="unknown")
    lines = [
        f"# Dry-Run Run Packet Review Required: {work_item_id}",
        "",
        "> This diagnostic packet is dry-run/manual and non-mutating. "
        "No agent, branch, pull request, merge, release, publish, or "
        "execution behavior has been invoked.",
        "",
        "## Work Item",
        "",
        f"- ID: `{work_item_id}`",
        f"- Title: {title}",
        f"- Status: `{status}`",
        f"- Source path: `{_display_path(path, project_root)}`",
        "",
        "## Missing Readiness Fields / Review Tasks",
        "",
    ]
    for issue in diagnostics:
        lines.append(f"- `{issue.code}`: {issue.message}")
    lines.extend(
        [
            "",
            "## Required Human Action",
            "",
            "- Update the source work item with the readiness metadata required "
            "for an executable leaf, or choose a different work item.",
            "- Re-run packet generation only after readiness metadata has been "
            "reviewed.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _extract_sections(body: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in body.splitlines():
        match = _SECTION_HEADING_RE.match(line)
        if match is not None:
            current = match.group(1).strip().lower()
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(line)
    return {name: "\n".join(lines).strip() for name, lines in sections.items()}


def _section_or_fallback(
    sections: dict[str, str], names: tuple[str, ...], fallback: str
) -> str:
    for name in names:
        value = sections.get(name)
        if value:
            return value
    return fallback


def _string_field(frontmatter: dict[str, Any], key: str, *, default: str) -> str:
    value = frontmatter.get(key)
    return value if isinstance(value, str) and value.strip() else default


def _list_field(frontmatter: dict[str, Any], key: str) -> tuple[str, ...]:
    value = frontmatter.get(key)
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item.strip())


def _forbidden_actions(frontmatter: dict[str, Any]) -> tuple[str, ...]:
    values = list(_list_field(frontmatter, "forbidden_actions"))
    safe_default_forbidden = [
        "invoke agents or backend adapters",
        "create, mutate, or delete branches",
        "create or mutate pull requests",
        "merge, release, publish, or perform destructive operations",
    ]
    for action in safe_default_forbidden:
        if action not in values:
            values.append(action)
    return tuple(values)


def _expected_artifacts(
    frontmatter: dict[str, Any],
    readiness: execution_readiness.ExecutionReadiness,
) -> tuple[str, ...]:
    if readiness.expected_artifacts:
        return readiness.expected_artifacts
    return _list_field(frontmatter, "artifacts_expected")


def _bullet_values(label: str, values: tuple[str, ...]) -> list[str]:
    if not values:
        return [f"- {label}: none"]
    return [f"- {label}: {', '.join(f'`{value}`' for value in values)}"]


def _labeled_list(label: str, values: tuple[str, ...]) -> list[str]:
    lines = [f"- {label}:"]
    if not values:
        lines.append("  - none")
        return lines
    for value in values:
        lines.append(f"  - {value}")
    return lines


def _list_lines(values: tuple[str, ...], *, code: bool = False) -> list[str]:
    if not values:
        return ["- none"]
    lines = []
    for value in values:
        lines.append(f"- `{value}`" if code else f"- {value}")
    return lines


def _display_path(path: pathlib.Path, project_root: pathlib.Path | str | None) -> str:
    if project_root is not None:
        try:
            return (
                path.resolve()
                .relative_to(pathlib.Path(project_root).resolve())
                .as_posix()
            )
        except ValueError:
            pass
    return path.as_posix()


def _optional_int(value: int | None) -> str:
    if value is None:
        return "not specified"
    return str(value)


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"
