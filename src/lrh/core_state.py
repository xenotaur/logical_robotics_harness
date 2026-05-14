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
class PromptRenderingInputs:
    """Small deterministic input set for request/snapshot prompt renderers."""

    project_name: str
    current_focus_id: str
    current_focus_title: str
    active_leaf_work_item_ids: tuple[str, ...]
    active_workstream_ids: tuple[str, ...]
    validation_is_valid: bool


@dataclass(frozen=True)
class CoreProjectState:
    """Shared read-only project-state summary for CLI and assist consumers."""

    identity: ProjectIdentity
    loaded_project: control_models.ProjectState
    validation: ValidationSummary
    planning: control_planning_tree.PlanningTreeIndex
    current_focus: FocusState
    workstreams: tuple[WorkstreamState, ...]
    work_items: tuple[WorkItemState, ...]
    active_leaf_work_items: tuple[WorkItemState, ...]
    evidence_links: tuple[EvidenceLink, ...]
    prompt_inputs: PromptRenderingInputs

    @property
    def work_items_by_id(self) -> dict[str, WorkItemState]:
        """Return a typed work-item state index keyed by work-item ID."""

        return {item.id: item for item in self.work_items}

    @property
    def workstreams_by_id(self) -> dict[str, WorkstreamState]:
        """Return a typed workstream state index keyed by workstream ID."""

        return {workstream.id: workstream for workstream in self.workstreams}


def load_core_project_state(root: Path) -> CoreProjectState:
    """Load deterministic shared project state from a repository or project root."""

    project_dir = control_loader.find_project_dir(root)
    project_root = _infer_project_root(project_dir)
    loaded_project = control_loader.load_project(project_dir)
    validation_report = control_validator.validate_project(project_dir)
    planning = control_planning_tree.build_planning_tree(loaded_project)

    validation = _validation_summary(validation_report)
    identity = ProjectIdentity(
        project_root=project_root,
        project_dir=project_dir,
        project_name=project_root.name,
    )
    current_focus = _focus_state(loaded_project.current_focus)
    workstreams = _workstream_states(loaded_project.workstreams, planning)
    work_items = _work_item_states(loaded_project, planning)
    active_leaf_work_items = tuple(item for item in work_items if item.is_active_leaf)
    evidence_links = _evidence_links(loaded_project)
    prompt_inputs = PromptRenderingInputs(
        project_name=identity.project_name,
        current_focus_id=current_focus.id,
        current_focus_title=current_focus.title,
        active_leaf_work_item_ids=tuple(item.id for item in active_leaf_work_items),
        active_workstream_ids=tuple(
            workstream.id for workstream in workstreams if workstream.status == "active"
        ),
        validation_is_valid=validation.is_valid,
    )

    return CoreProjectState(
        identity=identity,
        loaded_project=loaded_project,
        validation=validation,
        planning=planning,
        current_focus=current_focus,
        workstreams=workstreams,
        work_items=work_items,
        active_leaf_work_items=active_leaf_work_items,
        evidence_links=evidence_links,
        prompt_inputs=prompt_inputs,
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
