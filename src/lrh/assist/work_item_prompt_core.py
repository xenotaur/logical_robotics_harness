"""Core deterministic pipeline for generating Codex Cloud prompts from work items."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from lrh.control import parser as control_parser

_SECTION_HEADING_RE = re.compile(r"^##\s+(?P<name>[^\n]+)$", re.MULTILINE)


@dataclass(frozen=True)
class ParsedWorkItem:
    """Structured representation of an LRH work item markdown document."""

    source_path: Path
    work_item_id: str
    title: str
    status: str
    item_type: str
    blocked: bool
    summary: str
    problem: str
    scope: str
    out_of_scope: str
    required_changes: str
    likely_files: tuple[str, ...]
    validation: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    notes: str
    risk_level: str
    execution_suitability: str


@dataclass(frozen=True)
class PromptReadinessResult:
    """Readiness classification for Codex-cloud implementation prompting."""

    is_ready: bool
    blocking_reasons: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class WorkItemPromptData:
    """Resolved prompt data used to render a final Codex Cloud prompt."""

    prompt_id: str
    work_item_path: str
    style_guide_path: str
    work_item_id: str
    work_item_title: str
    objective: str
    strict_scope: tuple[str, ...]
    required_changes: tuple[str, ...]
    do_not: tuple[str, ...]
    validation: tuple[str, ...]
    success_criteria: tuple[str, ...]
    edge_case_rules: tuple[str, ...]
    final_check: tuple[str, ...]
    readiness: PromptReadinessResult


def parse_work_item_markdown(work_item_path: Path) -> ParsedWorkItem:
    """Parse one LRH work item markdown file into structured data."""
    parsed = control_parser.parse_markdown_file(work_item_path)
    frontmatter = parsed.frontmatter
    sections = _parse_sections(parsed.body)

    work_item_id = _string_value(frontmatter.get("id"), "id")
    title = _string_value(frontmatter.get("title"), "title")
    status = _string_value(frontmatter.get("status"), "status")
    item_type = _string_value(frontmatter.get("type"), "type")
    blocked = bool(frontmatter.get("blocked", False))

    return ParsedWorkItem(
        source_path=work_item_path,
        work_item_id=work_item_id,
        title=title,
        status=status,
        item_type=item_type,
        blocked=blocked,
        summary=sections.get("summary", ""),
        problem=sections.get("problem", ""),
        scope=sections.get("scope", ""),
        out_of_scope=sections.get("out of scope", sections.get("non-goals", "")),
        required_changes=sections.get("required changes", ""),
        likely_files=_extract_bullets(sections.get("likely files", "")),
        validation=_extract_bullets(sections.get("validation", "")),
        acceptance_criteria=_extract_bullets(sections.get("acceptance criteria", ""))
        or _extract_frontmatter_list(frontmatter.get("acceptance")),
        notes=sections.get("notes", ""),
        risk_level=sections.get("risk level", ""),
        execution_suitability=sections.get("execution suitability", ""),
    )


def evaluate_prompt_readiness(parsed: ParsedWorkItem) -> PromptReadinessResult:
    """Evaluate if a parsed work item is safe to convert to an implementation prompt."""
    blocking_reasons: list[str] = []
    warnings: list[str] = []

    if parsed.blocked:
        blocking_reasons.append("work item is marked blocked")

    if parsed.status in {"resolved", "abandoned"}:
        blocking_reasons.append(
            f"work item status '{parsed.status}' is not implementation-ready"
        )

    suitability = parsed.execution_suitability.lower()
    if "human design review first" in suitability:
        blocking_reasons.append(
            "execution suitability requires human design review first"
        )
    elif "human-suitable" in suitability:
        blocking_reasons.append(
            "execution suitability indicates human-only implementation"
        )

    if not parsed.scope:
        warnings.append("missing Scope section")
    if not parsed.required_changes:
        warnings.append("missing Required Changes section")
    if not parsed.acceptance_criteria:
        warnings.append("missing Acceptance Criteria")
    if not parsed.validation:
        warnings.append("missing Validation commands")

    return PromptReadinessResult(
        is_ready=not blocking_reasons,
        blocking_reasons=tuple(blocking_reasons),
        warnings=tuple(warnings),
    )


def build_work_item_prompt_data(
    *,
    parsed: ParsedWorkItem,
    readiness: PromptReadinessResult,
    prompt_id: str,
    work_item_path: str,
    style_guide_path: str,
) -> WorkItemPromptData:
    """Convert parsed work item + readiness result into deterministic prompt data."""
    objective = parsed.problem or parsed.summary or parsed.title

    strict_scope = _extract_bullets(parsed.scope)
    if not strict_scope and parsed.scope:
        strict_scope = tuple(line for line in _normalized_lines(parsed.scope))

    required_changes = _extract_bullets(parsed.required_changes)
    if not required_changes and parsed.required_changes:
        required_changes = tuple(
            line for line in _normalized_lines(parsed.required_changes)
        )

    do_not = _extract_bullets(parsed.out_of_scope)
    if not do_not and parsed.out_of_scope:
        do_not = tuple(line for line in _normalized_lines(parsed.out_of_scope))

    if parsed.likely_files:
        required_changes = required_changes + tuple(
            [
                "Keep edits constrained to likely files: "
                f"{', '.join(parsed.likely_files)}"
            ]
        )

    edge_case_rules = (
        "If requirements are ambiguous, stay conservative and report "
        "uncertainty instead of guessing.",
    )
    if readiness.warnings:
        warning_text = "; ".join(readiness.warnings)
        edge_case_rules = edge_case_rules + (
            f"Work-item structure warnings detected: {warning_text}.",
        )

    final_check = (
        "Scope remains limited to this single work item.",
        "No unrelated cleanup/refactors were introduced.",
        "Validation commands were run or clearly reported if blocked.",
    )

    return WorkItemPromptData(
        prompt_id=prompt_id,
        work_item_path=work_item_path,
        style_guide_path=style_guide_path,
        work_item_id=parsed.work_item_id,
        work_item_title=parsed.title,
        objective=objective,
        strict_scope=strict_scope,
        required_changes=required_changes,
        do_not=do_not,
        validation=parsed.validation,
        success_criteria=parsed.acceptance_criteria,
        edge_case_rules=edge_case_rules,
        final_check=final_check,
        readiness=readiness,
    )


def render_codex_cloud_prompt(data: WorkItemPromptData) -> str:
    """Render the final deterministic Codex Cloud implementation prompt markdown."""
    if not data.readiness.is_ready:
        reasons = "\n".join(f"- {reason}" for reason in data.readiness.blocking_reasons)
        return (
            "# Work Item Not Ready for Codex Implementation\n\n"
            f"Prompt ID: `{data.prompt_id}`\n\n"
            "This work item is not currently suitable for a direct Codex "
            "implementation prompt.\n\n"
            "## Blocking Reasons\n"
            f"{reasons}\n\n"
            "## Recommended Next Step\n"
            "Refine the work item and rerun prompt generation.\n"
        )

    return "\n".join(
        [
            "# ROLE",
            "",
            "You are a senior Python engineer making a single, tightly "
            "scoped repository change.",
            "",
            "# AUTHORITATIVE REFERENCES",
            "",
            f"- Prompt ID: `{data.prompt_id}`",
            f"- STYLE.md path: `{data.style_guide_path}`",
            f"- Approved work item: `{data.work_item_path}`",
            "",
            "# OBJECTIVE",
            "",
            data.objective,
            "",
            "# STRICT SCOPE",
            "",
            _render_bullets(data.strict_scope),
            "",
            "# REQUIRED CHANGES",
            "",
            _render_bullets(data.required_changes),
            "",
            "# DO NOT",
            "",
            _render_bullets(data.do_not),
            "",
            "# EDGE CASE RULES",
            "",
            _render_bullets(data.edge_case_rules),
            "",
            "# VALIDATION",
            "",
            _render_bullets(data.validation),
            "",
            "# OUTPUT REQUIREMENTS",
            "",
            "- Summarize files changed and why.",
            "- Report validation commands and outcomes.",
            "- Explicitly list intentionally untouched areas.",
            "",
            "# SUCCESS CRITERIA",
            "",
            _render_bullets(data.success_criteria),
            "",
            "# FINAL CHECK",
            "",
            _render_bullets(data.final_check),
            "",
            "# BEGIN",
        ]
    )


def generate_codex_cloud_prompt(
    *,
    prompt_id: str,
    work_item_path: Path,
    style_guide_path: str,
    work_item_reference_path: str | None = None,
) -> str:
    """Deterministic full pipeline for generating final prompt markdown."""
    parsed = parse_work_item_markdown(work_item_path)
    readiness = evaluate_prompt_readiness(parsed)
    data = build_work_item_prompt_data(
        parsed=parsed,
        readiness=readiness,
        prompt_id=prompt_id,
        work_item_path=work_item_reference_path or work_item_path.as_posix(),
        style_guide_path=style_guide_path,
    )
    return render_codex_cloud_prompt(data)


def _string_value(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"work item frontmatter field '{field_name}' must be a string")
    return value.strip()


def _parse_sections(markdown_body: str) -> dict[str, str]:
    matches = list(_SECTION_HEADING_RE.finditer(markdown_body))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(markdown_body)
        )
        title = match.group("name").strip().lower()
        sections[title] = markdown_body[start:end].strip()
    return sections


def _extract_bullets(section_text: str) -> tuple[str, ...]:
    bullets: list[str] = []
    current_parts: list[str] = []

    for line in section_text.splitlines():
        stripped = line.strip()

        if stripped.startswith("- "):
            if current_parts:
                bullets.append(" ".join(current_parts))
            current_parts = [stripped[2:].strip()]
            continue

        if not current_parts:
            continue

        if not stripped:
            continue

        if line.startswith(" ") or line.startswith("\t"):
            current_parts.append(stripped)
            continue

        bullets.append(" ".join(current_parts))
        current_parts = []

    if current_parts:
        bullets.append(" ".join(current_parts))

    return tuple(bullets)


def _extract_frontmatter_list(value: object) -> tuple[str, ...]:
    if isinstance(value, list):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return ()


def _render_bullets(values: tuple[str, ...]) -> str:
    if not values:
        return "- (none provided)"
    return "\n".join(f"- {value}" for value in values)


def _normalized_lines(value: str) -> tuple[str, ...]:
    return tuple(line.strip() for line in value.splitlines() if line.strip())
