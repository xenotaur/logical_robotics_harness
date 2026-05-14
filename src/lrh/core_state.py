"""Read-only shared project-state interpretation APIs.

The core-state API composes the existing control-plane loader, validator, and
planning-tree index into deterministic typed summaries. It is intentionally
read-only: callers can inspect project state, validation diagnostics, planning
relationships, and prompt-rendering inputs without gaining any repository
mutation or runtime execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from lrh.control import loader as control_loader
from lrh.control import models as control_models
from lrh.control import planning_tree as control_planning_tree
from lrh.control import validator as control_validator


@dataclass(frozen=True)
class ProjectIdentity:
    """Stable identity for a loaded project control directory."""

    project_root: Path
    project_dir: Path
    project_name: str


@dataclass(frozen=True)
class DiagnosticSummary:
    """Deterministic diagnostic summary from validation or planning checks."""

    source: str
    file: str
    severity: str
    code: str
    message: str


@dataclass(frozen=True)
class ValidationSummary:
    """Validation state suitable for status and readiness consumers."""

    is_valid: bool
    error_count: int
    warning_count: int
    diagnostics: tuple[DiagnosticSummary, ...]


@dataclass(frozen=True)
class FocusState:
    """Typed current-focus summary with source-document references."""

    id: str
    title: str
    status: str
    priority: str | None
    owner: str | None
    path: Path
    related_principles: tuple[str, ...]
    frontmatter_keys: tuple[str, ...]


@dataclass(frozen=True)
class WorkItemState:
    """Read-only work-item state enriched with planning relationships."""

    id: str
    title: str
    type: str
    status: str
    priority: str | None
    owner: str | None
    path: Path
    parent_ids: tuple[str, ...]
    child_ids: tuple[str, ...]
    related_focus: tuple[str, ...]
    depends_on: tuple[str, ...]
    blocked_by: tuple[str, ...]
    required_evidence: tuple[str, ...]
    artifacts_expected: tuple[str, ...]
    is_current_focus_related: bool
    is_active_leaf: bool
    frontmatter_keys: tuple[str, ...]


@dataclass(frozen=True)
class WorkstreamState:
    """Read-only workstream planning-node state."""

    id: str
    title: str
    status: str
    stage: str
    bucket: str | None
    path: Path
    parent_ids: tuple[str, ...]
    child_ids: tuple[str, ...]
    work_items: tuple[str, ...]
    evidence: tuple[str, ...]
    frontmatter_keys: tuple[str, ...]


@dataclass(frozen=True)
class EvidenceLink:
    """Evidence/status reference declared by a typed control-plane artifact."""

    source_id: str
    source_kind: str
    field: str
    target: str


@dataclass(frozen=True)
class PlanningRelationshipState:
    """Read-only parent/child planning relationship summary."""

    parent_id: str
    child_id: str
    source_id: str
    source_field: str


@dataclass(frozen=True)
class PlanningState:
    """Read-only planning-tree summary without mutable backing indexes."""

    relationships: tuple[PlanningRelationshipState, ...]
    diagnostics: tuple[DiagnosticSummary, ...]
    cycles: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class PromptRenderingInputs:
    """Small deterministic input set for request/snapshot prompt renderers."""

    project_name: str
    current_focus_id: str | None
    current_focus_title: str | None
    active_leaf_work_item_ids: tuple[str, ...]
    active_workstream_ids: tuple[str, ...]
    validation_is_valid: bool


@dataclass(frozen=True)
class CoreProjectState:
    """Shared read-only project-state summary for CLI and assist consumers."""

    identity: ProjectIdentity
    validation: ValidationSummary
    planning: PlanningState
    current_focus: FocusState | None
    workstreams: tuple[WorkstreamState, ...]
    work_items: tuple[WorkItemState, ...]
    active_leaf_work_items: tuple[WorkItemState, ...]
    evidence_links: tuple[EvidenceLink, ...]
    prompt_inputs: PromptRenderingInputs
    work_items_by_id: Mapping[str, WorkItemState]
    workstreams_by_id: Mapping[str, WorkstreamState]


def load_core_project_state(
    root: Path,
    *,
    validation_report: control_validator.ValidationReport | None = None,
    validate: bool = True,
) -> CoreProjectState:
    """Load deterministic shared project state from a repository or project root.

    Validation runs before strict typed loading by default so validation-reportable
    structural errors return diagnostics instead of raising from loader indexing.
    Callers that already validated may pass ``validation_report`` to avoid
    re-running validation, or set ``validate=False`` when they intentionally want
    loader-only interpretation.
    """

    project_dir = control_loader.find_project_dir(root)
    project_root = _infer_project_root(project_dir)
    identity = ProjectIdentity(
        project_root=project_root,
        project_dir=project_dir,
        project_name=project_root.name,
    )
    report = _resolve_validation_report(
        project_dir,
        validation_report=validation_report,
        validate=validate,
    )
    validation = _validation_summary(report)
    if validation.error_count:
        return _empty_core_project_state(identity, validation)

    loaded_project = control_loader.load_project(project_dir)
    planning_index = control_planning_tree.build_planning_tree(loaded_project)

    current_focus = _focus_state(loaded_project.current_focus)
    workstreams = _workstream_states(loaded_project.workstreams, planning_index)
    work_items = _work_item_states(loaded_project, planning_index)
    active_leaf_work_items = tuple(item for item in work_items if item.is_active_leaf)
    evidence_links = _evidence_links(loaded_project)
    prompt_inputs = _prompt_inputs(
        identity=identity,
        current_focus=current_focus,
        workstreams=workstreams,
        active_leaf_work_items=active_leaf_work_items,
        validation=validation,
    )

    return CoreProjectState(
        identity=identity,
        validation=validation,
        planning=_planning_state(project_dir, planning_index),
        current_focus=current_focus,
        workstreams=workstreams,
        work_items=work_items,
        active_leaf_work_items=active_leaf_work_items,
        evidence_links=evidence_links,
        prompt_inputs=prompt_inputs,
        work_items_by_id=_read_only_index(work_items),
        workstreams_by_id=_read_only_index(workstreams),
    )


def _resolve_validation_report(
    project_dir: Path,
    *,
    validation_report: control_validator.ValidationReport | None,
    validate: bool,
) -> control_validator.ValidationReport:
    if validation_report is not None:
        return validation_report
    if validate:
        return control_validator.validate_project(project_dir)
    return control_validator.ValidationReport(issues=[])


def _empty_core_project_state(
    identity: ProjectIdentity,
    validation: ValidationSummary,
) -> CoreProjectState:
    return CoreProjectState(
        identity=identity,
        validation=validation,
        planning=PlanningState(relationships=(), diagnostics=(), cycles=()),
        current_focus=None,
        workstreams=(),
        work_items=(),
        active_leaf_work_items=(),
        evidence_links=(),
        prompt_inputs=PromptRenderingInputs(
            project_name=identity.project_name,
            current_focus_id=None,
            current_focus_title=None,
            active_leaf_work_item_ids=(),
            active_workstream_ids=(),
            validation_is_valid=validation.is_valid,
        ),
        work_items_by_id=MappingProxyType({}),
        workstreams_by_id=MappingProxyType({}),
    )


def _infer_project_root(project_dir: Path) -> Path:
    if project_dir.name == "project":
        return project_dir.parent
    return project_dir


def _validation_summary(
    report: control_validator.ValidationReport,
) -> ValidationSummary:
    diagnostics = [
        DiagnosticSummary(
            source="validate",
            file=issue.file,
            severity=issue.severity,
            code=issue.code,
            message=issue.message,
        )
        for issue in report.issues
    ]
    sorted_diagnostics = tuple(
        sorted(
            diagnostics,
            key=lambda diagnostic: (
                diagnostic.severity,
                diagnostic.file,
                diagnostic.code,
                diagnostic.message,
                diagnostic.source,
            ),
        )
    )
    return ValidationSummary(
        is_valid=not any(
            diagnostic.severity == "error" for diagnostic in sorted_diagnostics
        ),
        error_count=sum(
            1 for diagnostic in sorted_diagnostics if diagnostic.severity == "error"
        ),
        warning_count=sum(
            1 for diagnostic in sorted_diagnostics if diagnostic.severity == "warning"
        ),
        diagnostics=sorted_diagnostics,
    )


def _planning_state(
    project_dir: Path,
    index: control_planning_tree.PlanningTreeIndex,
) -> PlanningState:
    relationships = tuple(
        sorted(
            (
                PlanningRelationshipState(
                    parent_id=relationship.parent_id,
                    child_id=relationship.child_id,
                    source_id=relationship.source_id,
                    source_field=relationship.source_field,
                )
                for relationship in index.relationships
            ),
            key=lambda relationship: (
                relationship.parent_id,
                relationship.child_id,
                relationship.source_id,
                relationship.source_field,
            ),
        )
    )
    diagnostics = tuple(
        sorted(
            (
                DiagnosticSummary(
                    source="planning",
                    file=_relative_path(project_dir, diagnostic.path),
                    severity=diagnostic.severity,
                    code=diagnostic.code,
                    message=diagnostic.message,
                )
                for diagnostic in index.diagnostics
            ),
            key=lambda diagnostic: (
                diagnostic.severity,
                diagnostic.file,
                diagnostic.code,
                diagnostic.message,
                diagnostic.source,
            ),
        )
    )
    return PlanningState(
        relationships=relationships,
        diagnostics=diagnostics,
        cycles=tuple(sorted(index.cycles)),
    )


def _focus_state(focus: control_models.Focus) -> FocusState:
    return FocusState(
        id=focus.id,
        title=focus.title,
        status=focus.status,
        priority=focus.priority,
        owner=focus.owner,
        path=focus.path,
        related_principles=tuple(sorted(focus.related_principles)),
        frontmatter_keys=tuple(sorted(focus.frontmatter)),
    )


def _workstream_states(
    workstreams: tuple[control_models.Workstream, ...],
    planning: control_planning_tree.PlanningTreeIndex,
) -> tuple[WorkstreamState, ...]:
    states = [
        WorkstreamState(
            id=workstream.id,
            title=workstream.title,
            status=workstream.status,
            stage=workstream.stage,
            bucket=workstream.bucket,
            path=workstream.path,
            parent_ids=tuple(sorted(planning.parents_of(workstream.id))),
            child_ids=tuple(sorted(planning.children_of(workstream.id))),
            work_items=tuple(sorted(workstream.work_items)),
            evidence=tuple(sorted(workstream.evidence)),
            frontmatter_keys=tuple(sorted(workstream.frontmatter)),
        )
        for workstream in workstreams
    ]
    return tuple(sorted(states, key=lambda workstream: workstream.id))


def _work_item_states(
    loaded_project: control_models.ProjectState,
    planning: control_planning_tree.PlanningTreeIndex,
) -> tuple[WorkItemState, ...]:
    current_focus_id = loaded_project.current_focus.id
    states = []
    for item in loaded_project.work_items:
        child_ids = tuple(sorted(planning.children_of(item.id)))
        parent_ids = tuple(sorted(planning.parents_of(item.id)))
        is_current_focus_related = current_focus_id in item.related_focus
        states.append(
            WorkItemState(
                id=item.id,
                title=item.title,
                type=item.type,
                status=item.status,
                priority=item.priority,
                owner=item.owner,
                path=item.path,
                parent_ids=parent_ids,
                child_ids=child_ids,
                related_focus=tuple(sorted(item.related_focus)),
                depends_on=tuple(sorted(item.depends_on)),
                blocked_by=tuple(sorted(item.blocked_by)),
                required_evidence=tuple(sorted(item.required_evidence)),
                artifacts_expected=tuple(sorted(item.artifacts_expected)),
                is_current_focus_related=is_current_focus_related,
                is_active_leaf=(
                    item.status == "active"
                    and is_current_focus_related
                    and not child_ids
                ),
                frontmatter_keys=tuple(sorted(item.frontmatter)),
            )
        )
    return tuple(sorted(states, key=lambda item: item.id))


def _evidence_links(
    loaded_project: control_models.ProjectState,
) -> tuple[EvidenceLink, ...]:
    links: list[EvidenceLink] = []
    for work_item in loaded_project.work_items:
        links.extend(
            EvidenceLink(
                source_id=work_item.id,
                source_kind="work_item",
                field="required_evidence",
                target=evidence,
            )
            for evidence in work_item.required_evidence
        )
    for workstream in loaded_project.workstreams:
        links.extend(
            EvidenceLink(
                source_id=workstream.id,
                source_kind="workstream",
                field="evidence",
                target=evidence,
            )
            for evidence in workstream.evidence
        )
    for proposal in loaded_project.design_proposals:
        links.extend(
            EvidenceLink(
                source_id=proposal.id,
                source_kind="design_proposal",
                field="evidence",
                target=evidence,
            )
            for evidence in proposal.evidence
        )
    return tuple(
        sorted(
            links,
            key=lambda link: (
                link.source_kind,
                link.source_id,
                link.field,
                link.target,
            ),
        )
    )


def _prompt_inputs(
    *,
    identity: ProjectIdentity,
    current_focus: FocusState,
    workstreams: tuple[WorkstreamState, ...],
    active_leaf_work_items: tuple[WorkItemState, ...],
    validation: ValidationSummary,
) -> PromptRenderingInputs:
    return PromptRenderingInputs(
        project_name=identity.project_name,
        current_focus_id=current_focus.id,
        current_focus_title=current_focus.title,
        active_leaf_work_item_ids=tuple(item.id for item in active_leaf_work_items),
        active_workstream_ids=tuple(
            workstream.id for workstream in workstreams if workstream.status == "active"
        ),
        validation_is_valid=validation.is_valid,
    )


def _read_only_index(
    items: tuple[WorkItemState, ...] | tuple[WorkstreamState, ...],
) -> Mapping[str, WorkItemState] | Mapping[str, WorkstreamState]:
    return MappingProxyType({item.id: item for item in items})


def _relative_path(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)
