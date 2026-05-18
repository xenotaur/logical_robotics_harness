"""Assistive ready-work-item request rendering."""

from __future__ import annotations

import dataclasses
import pathlib
from collections.abc import Iterable

from lrh.assist import (
    request_service,
    request_templates,
    request_variables,
    work_item_prompt_core,
)
from lrh.control import parser as control_parser

_CONTEXT_FIELDS = (
    ("related_roadmap", "Roadmap", ("project/roadmap",)),
    ("related_focus", "Focus", ("project/focus",)),
    ("related_design", "Design", ("project/design",)),
    ("related_workstreams", "Workstream", ("project/workstreams",)),
    ("depends_on", "Dependency", ("project/work_items",)),
    ("related_status", "Status", ("project/status",)),
    ("related_evidence", "Evidence", ("project/evidence",)),
    ("evidence", "Evidence", ("project/evidence",)),
    ("related_executions", "Execution Record", ("project/executions",)),
    ("execution_records", "Execution Record", ("project/executions",)),
)

_REQUESTED_SECTIONS = (
    "Problem",
    "Scope",
    "Out of Scope",
    "Required Changes",
    "Likely Files",
    "Validation",
    "Acceptance Criteria",
    "Open Questions",
)


@dataclasses.dataclass(frozen=True)
class ResolvedContext:
    """One referenced context artifact resolved for a ready-work-item request."""

    relation: str
    reference: str
    path: str
    title: str
    status: str
    excerpt: str


@dataclasses.dataclass(frozen=True)
class UnresolvedContext:
    """One referenced context artifact that could not be resolved."""

    relation: str
    reference: str
    searched: tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class ReadyWorkItemRequest:
    """Rendered ready-work-item request and non-mutating diagnostics."""

    markdown: str
    readiness: work_item_prompt_core.PromptReadinessResult
    resolved_context: tuple[ResolvedContext, ...]
    unresolved_context: tuple[UnresolvedContext, ...]


def render_ready_work_item_request(
    work_item_path: str | pathlib.Path,
    *,
    project_root: pathlib.Path | None = None,
    template_root: pathlib.Path | None = None,
    template_dirs: list[pathlib.Path | str] | None = None,
) -> ReadyWorkItemRequest:
    """Render a non-mutating readiness-refinement request for one work item."""
    resolved_work_item_path = pathlib.Path(work_item_path)
    resolved_project_root = _resolve_project_root(project_root, resolved_work_item_path)

    parsed = work_item_prompt_core.parse_work_item_markdown(resolved_work_item_path)
    readiness = work_item_prompt_core.evaluate_prompt_readiness(parsed)
    source_document = control_parser.parse_markdown_file(resolved_work_item_path)
    resolved_context, unresolved_context = _resolve_referenced_context(
        frontmatter=source_document.frontmatter,
        project_root=resolved_project_root,
    )

    variables = {
        "TARGET_WORK_ITEM_ID": parsed.work_item_id,
        "TARGET_WORK_ITEM_TITLE": parsed.title,
        "TARGET_WORK_ITEM_STATUS": parsed.status,
        "TARGET_WORK_ITEM_TYPE": parsed.item_type,
        "TARGET_WORK_ITEM_PATH": _display_path(
            resolved_work_item_path,
            project_root=resolved_project_root,
        ),
        "READINESS_STATUS": "ready" if readiness.is_ready else "not ready",
        "READINESS_DIAGNOSTICS": _render_readiness_diagnostics(readiness),
        "REFERENCED_CONTEXT": _render_referenced_context(
            resolved_context,
            unresolved_context,
        ),
        "REQUESTED_SECTIONS": _render_bullets(_REQUESTED_SECTIONS),
        "WORK_ITEM_CONTENT": resolved_work_item_path.read_text(encoding="utf-8"),
    }
    template_text = request_templates.load_template_text(
        "ready_work_item",
        template_root=template_root,
        project_root=resolved_project_root,
        template_dirs=template_dirs,
    )
    rendered = request_service.render_template(template_text, variables)
    return ReadyWorkItemRequest(
        markdown=rendered,
        readiness=readiness,
        resolved_context=resolved_context,
        unresolved_context=unresolved_context,
    )


def _resolve_project_root(
    project_root: pathlib.Path | None,
    work_item_path: pathlib.Path,
) -> pathlib.Path:
    if project_root is not None:
        return project_root.resolve()
    repo_root = request_variables.find_repo_root()
    if repo_root is not None:
        return repo_root.resolve()
    return work_item_path.resolve().parent


def _resolve_referenced_context(
    *,
    frontmatter: dict[str, object],
    project_root: pathlib.Path,
) -> tuple[tuple[ResolvedContext, ...], tuple[UnresolvedContext, ...]]:
    resolved: list[ResolvedContext] = []
    unresolved: list[UnresolvedContext] = []
    for field_name, label, search_roots in _CONTEXT_FIELDS:
        references = _string_references(frontmatter.get(field_name))
        for reference in references:
            match, searched = _resolve_reference(
                reference=reference,
                project_root=project_root,
                search_roots=search_roots,
            )
            if match is None:
                unresolved.append(
                    UnresolvedContext(
                        relation=label,
                        reference=reference,
                        searched=tuple(searched),
                    )
                )
            else:
                resolved.append(
                    _build_resolved_context(
                        relation=label,
                        reference=reference,
                        path=match,
                        project_root=project_root,
                    )
                )
    return tuple(resolved), tuple(unresolved)


def _resolve_reference(
    *,
    reference: str,
    project_root: pathlib.Path,
    search_roots: tuple[str, ...],
) -> tuple[pathlib.Path | None, list[str]]:
    reference_path = pathlib.Path(reference)
    direct_candidates = []
    if reference_path.is_absolute():
        direct_candidates.append(reference_path)
    else:
        direct_candidates.append(project_root / reference_path)
    if not reference.lower().endswith(".md"):
        direct_candidates.append(project_root / f"{reference}.md")

    searched: list[str] = []
    for candidate in direct_candidates:
        searched.append(_display_path(candidate, project_root=project_root))
        if candidate.is_file():
            return candidate, searched

    for root_name in search_roots:
        root = project_root / root_name
        searched.append(f"{root_name}/**/*.md")
        if not root.is_dir():
            continue
        matches = _find_markdown_reference_matches(root=root, reference=reference)
        if len(matches) == 1:
            return matches[0], searched
        if len(matches) > 1:
            return None, searched
    return None, searched


def _find_markdown_reference_matches(
    *, root: pathlib.Path, reference: str
) -> list[pathlib.Path]:
    reference_stem = pathlib.Path(reference).stem
    matches: list[pathlib.Path] = []
    for path in sorted(root.glob("**/*.md")):
        if not path.is_file():
            continue
        if path.stem == reference_stem or path.name == reference:
            matches.append(path)
            continue
        try:
            parsed = control_parser.parse_markdown_file(path)
        except (FileNotFoundError, OSError, UnicodeDecodeError, ValueError):
            continue
        document_id = parsed.frontmatter.get("id")
        if isinstance(document_id, str) and document_id == reference:
            matches.append(path)
    return matches


def _build_resolved_context(
    *, relation: str, reference: str, path: pathlib.Path, project_root: pathlib.Path
) -> ResolvedContext:
    title = ""
    status = ""
    excerpt = ""
    try:
        parsed = control_parser.parse_markdown_file(path)
        title = _frontmatter_string(parsed.frontmatter.get("title"))
        status = _frontmatter_string(parsed.frontmatter.get("status"))
        excerpt = _excerpt(parsed.body)
    except (FileNotFoundError, OSError, UnicodeDecodeError, ValueError):
        excerpt = "(Unable to parse context body.)"
    return ResolvedContext(
        relation=relation,
        reference=reference,
        path=_display_path(path, project_root=project_root),
        title=title,
        status=status,
        excerpt=excerpt,
    )


def _render_readiness_diagnostics(
    readiness: work_item_prompt_core.PromptReadinessResult,
) -> str:
    if readiness.is_ready and not readiness.warnings:
        return "- No blocking prompt-readiness diagnostics were reported."
    lines: list[str] = []
    if readiness.blocking_reasons:
        lines.append("Blocking reasons:")
        lines.extend(f"- {reason}" for reason in readiness.blocking_reasons)
    if readiness.warnings:
        if lines:
            lines.append("")
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in readiness.warnings)
    return "\n".join(lines)


def _render_referenced_context(
    resolved: tuple[ResolvedContext, ...],
    unresolved: tuple[UnresolvedContext, ...],
) -> str:
    if not resolved and not unresolved:
        return "No frontmatter relationship context was discovered."

    lines: list[str] = []
    if resolved:
        lines.append("## Resolved Context")
        for context in resolved:
            title = f" — {context.title}" if context.title else ""
            status = f" (status: {context.status})" if context.status else ""
            context_line = (
                f"- {context.relation}: `{context.reference}` -> "
                f"`{context.path}`{title}{status}"
            )
            lines.append(context_line)
            if context.excerpt:
                lines.append(f"  - Excerpt: {context.excerpt}")
    if unresolved:
        if lines:
            lines.append("")
        lines.append("## Unresolved Context")
        for context in unresolved:
            searched = ", ".join(f"`{item}`" for item in context.searched)
            lines.append(
                f"- {context.relation}: `{context.reference}` was not resolved. "
                f"Searched: {searched}. Treat this as an open question."
            )
    return "\n".join(lines)


def _render_bullets(values: Iterable[str]) -> str:
    return "\n".join(f"- `## {value}`" for value in values)


def _string_references(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        stripped = value.strip()
        return (stripped,) if stripped else ()
    if isinstance(value, (list, tuple)):
        references: list[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                references.append(item.strip())
        return tuple(references)
    return ()


def _frontmatter_string(value: object) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _excerpt(body: str, *, max_chars: int = 360) -> str:
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    if not lines:
        return ""
    text = " ".join(lines)
    if len(text) <= max_chars:
        return text
    return f"{text[: max_chars - 1].rstrip()}…"


def _display_path(path: pathlib.Path, *, project_root: pathlib.Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()
