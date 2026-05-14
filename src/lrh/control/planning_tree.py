"""Relationship index for workstreams and work-item planning leaves."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from lrh.control.models import ProjectState, WorkItem, Workstream

ARTIFACT_WORK_ITEM = "work_item"
ARTIFACT_WORKSTREAM = "workstream"
RELATION_CHILDREN = "children"
RELATION_PARENT_ID = "parent_id"
RELATION_WORK_ITEMS = "work_items"


@dataclass(frozen=True)
class PlanningArtifact:
    """Indexed planning artifact addressable by durable metadata ID."""

    id: str
    kind: str
    path: Path
    status: str
    title: str = ""
    related_focus: tuple[str, ...] = ()
    related_roadmap: tuple[str, ...] = ()
    related_workstreams: tuple[str, ...] = ()
    related_design: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()
    is_active_leaf: bool = False


@dataclass(frozen=True)
class PlanningRelationship:
    """Parent-to-child relationship inferred from source metadata."""

    parent_id: str
    child_id: str
    source_id: str
    source_field: str


@dataclass(frozen=True)
class PlanningDiagnostic:
    """Relationship-index diagnostic suitable for validation integration."""

    artifact_id: str
    path: Path
    severity: str
    code: str
    message: str


@dataclass(frozen=True)
class PlanningTreeIndex:
    """Metadata-driven planning relationship index.

    Workstreams are planning nodes. Work items are executable leaves. IDs are the
    only durable relationship addresses; filesystem nesting is intentionally not
    interpreted as a parent/child relationship.
    """

    artifacts_by_id: dict[str, PlanningArtifact]
    relationships: tuple[PlanningRelationship, ...]
    children_by_parent_id: dict[str, tuple[str, ...]]
    parents_by_child_id: dict[str, tuple[str, ...]]
    diagnostics: tuple[PlanningDiagnostic, ...]
    cycles: tuple[tuple[str, ...], ...]

    def children_of(self, artifact_id: str) -> tuple[str, ...]:
        """Return children inferred for a parent artifact ID."""

        return self.children_by_parent_id.get(artifact_id, ())

    def parents_of(self, artifact_id: str) -> tuple[str, ...]:
        """Return parents inferred for a child artifact ID."""

        return self.parents_by_child_id.get(artifact_id, ())

    def roots(self) -> tuple[str, ...]:
        """Return top-level workstream IDs with no inferred parent workstream."""

        return tuple(
            artifact_id
            for artifact_id, artifact in self.artifacts_by_id.items()
            if artifact.kind == ARTIFACT_WORKSTREAM
            and artifact_id not in self.parents_by_child_id
        )

    def active_leaf_ids(self) -> tuple[str, ...]:
        """Return active work-item leaf IDs suitable for readiness summaries."""

        return tuple(
            sorted(
                artifact_id
                for artifact_id, artifact in self.artifacts_by_id.items()
                if artifact.is_active_leaf
            )
        )

    def status_counts_by_kind(self) -> dict[str, dict[str, int]]:
        """Return status counts grouped by planning artifact kind."""

        counts: dict[str, dict[str, int]] = {}
        for artifact in self.artifacts_by_id.values():
            kind_counts = counts.setdefault(artifact.kind, {})
            kind_counts[artifact.status] = kind_counts.get(artifact.status, 0) + 1
        return {
            kind: dict(sorted(kind_counts.items()))
            for kind, kind_counts in sorted(counts.items())
        }

    def unresolved_references(self) -> tuple[PlanningDiagnostic, ...]:
        """Return diagnostics for references that could not be resolved by ID."""

        return tuple(
            diagnostic
            for diagnostic in self.diagnostics
            if diagnostic.code
            in {
                "PLANNING_UNKNOWN_PARENT_ID",
                "PLANNING_UNKNOWN_CHILD_ID",
            }
        )


def build_planning_tree(project_state: ProjectState) -> PlanningTreeIndex:
    """Build a reusable planning-tree relationship index for loaded project state."""

    return build_planning_tree_from_artifacts(
        workstreams=project_state.workstreams,
        work_items=project_state.work_items,
    )


def build_planning_tree_from_artifacts(
    *,
    workstreams: tuple[Workstream, ...],
    work_items: tuple[WorkItem, ...],
) -> PlanningTreeIndex:
    """Build a relationship index from typed workstreams and work items."""

    artifacts_by_id: dict[str, PlanningArtifact] = {}
    diagnostics: list[PlanningDiagnostic] = []

    _index_artifacts(artifacts_by_id, diagnostics, workstreams, ARTIFACT_WORKSTREAM)
    _index_artifacts(artifacts_by_id, diagnostics, work_items, ARTIFACT_WORK_ITEM)

    relationships: list[PlanningRelationship] = []
    _collect_workstream_relationships(
        artifacts_by_id,
        diagnostics,
        relationships,
        workstreams,
    )
    _collect_work_item_relationships(
        artifacts_by_id,
        diagnostics,
        relationships,
        work_items,
    )

    children_by_parent_id = _children_by_parent(relationships)
    parents_by_child_id = _parents_by_child(relationships)
    _mark_active_leaves(artifacts_by_id, children_by_parent_id)
    _detect_parent_child_mismatches(
        artifacts_by_id,
        diagnostics,
        workstreams,
        work_items,
        children_by_parent_id,
        parents_by_child_id,
    )

    _detect_active_state_gaps(
        artifacts_by_id,
        diagnostics,
        workstreams,
        work_items,
        children_by_parent_id,
        parents_by_child_id,
    )

    cycles = _find_workstream_cycles(artifacts_by_id, children_by_parent_id)
    for cycle in cycles:
        cycle_path = " -> ".join((*cycle, cycle[0]))
        first = artifacts_by_id[cycle[0]]
        diagnostics.append(
            PlanningDiagnostic(
                artifact_id=cycle[0],
                path=first.path,
                severity="error",
                code="PLANNING_NODE_CYCLE",
                message=f"planning node cycle detected: {cycle_path}",
            )
        )

    return PlanningTreeIndex(
        artifacts_by_id=artifacts_by_id,
        relationships=tuple(relationships),
        children_by_parent_id=children_by_parent_id,
        parents_by_child_id=parents_by_child_id,
        diagnostics=tuple(diagnostics),
        cycles=cycles,
    )


def _index_artifacts(
    artifacts_by_id: dict[str, PlanningArtifact],
    diagnostics: list[PlanningDiagnostic],
    artifacts: tuple[Workstream, ...] | tuple[WorkItem, ...],
    artifact_kind: str,
) -> None:
    for artifact in artifacts:
        if artifact.id in artifacts_by_id:
            existing = artifacts_by_id[artifact.id]
            diagnostics.append(
                PlanningDiagnostic(
                    artifact_id=artifact.id,
                    path=artifact.path,
                    severity="error",
                    code="PLANNING_DUPLICATE_ID",
                    message=(
                        f"duplicate planning artifact id '{artifact.id}' also used by "
                        f"{existing.kind} at {existing.path}"
                    ),
                )
            )
            continue
        artifacts_by_id[artifact.id] = _planning_artifact(artifact, artifact_kind)


def _planning_artifact(
    artifact: Workstream | WorkItem,
    artifact_kind: str,
) -> PlanningArtifact:
    related_design = getattr(artifact, "related_design", ())
    if artifact_kind == ARTIFACT_WORK_ITEM:
        return PlanningArtifact(
            id=artifact.id,
            kind=artifact_kind,
            path=artifact.path,
            status=artifact.status,
            title=artifact.title,
            related_focus=tuple(sorted(artifact.related_focus)),
            related_roadmap=tuple(sorted(artifact.related_roadmap)),
            related_workstreams=tuple(sorted(artifact.related_workstreams)),
            related_design=tuple(sorted(related_design)),
            dependencies=tuple(sorted(artifact.depends_on)),
            blockers=tuple(sorted(artifact.blocked_by)),
            evidence=tuple(sorted(artifact.required_evidence)),
        )
    return PlanningArtifact(
        id=artifact.id,
        kind=artifact_kind,
        path=artifact.path,
        status=artifact.status,
        title=artifact.title,
        related_focus=tuple(sorted(artifact.related_focus)),
        related_roadmap=tuple(sorted(artifact.related_roadmap)),
        related_design=tuple(sorted(related_design)),
        evidence=tuple(sorted(artifact.evidence)),
    )


def _collect_workstream_relationships(
    artifacts_by_id: dict[str, PlanningArtifact],
    diagnostics: list[PlanningDiagnostic],
    relationships: list[PlanningRelationship],
    workstreams: tuple[Workstream, ...],
) -> None:
    for workstream in workstreams:
        if workstream.id not in artifacts_by_id:
            continue
        if workstream.parent_id:
            _append_parent_id_relationship(
                artifacts_by_id,
                diagnostics,
                relationships,
                workstream.id,
                workstream.parent_id,
                workstream.path,
            )
        for child_id in workstream.children:
            _append_child_relationship(
                artifacts_by_id,
                diagnostics,
                relationships,
                workstream.id,
                child_id,
                RELATION_CHILDREN,
                workstream.path,
            )
        for child_id in workstream.work_items:
            _append_work_item_relationship(
                artifacts_by_id,
                diagnostics,
                relationships,
                workstream.id,
                child_id,
                workstream.path,
            )


def _collect_work_item_relationships(
    artifacts_by_id: dict[str, PlanningArtifact],
    diagnostics: list[PlanningDiagnostic],
    relationships: list[PlanningRelationship],
    work_items: tuple[WorkItem, ...],
) -> None:
    for work_item in work_items:
        if work_item.id not in artifacts_by_id:
            continue
        if work_item.parent_id:
            _append_parent_id_relationship(
                artifacts_by_id,
                diagnostics,
                relationships,
                work_item.id,
                work_item.parent_id,
                work_item.path,
            )


def _append_parent_id_relationship(
    artifacts_by_id: dict[str, PlanningArtifact],
    diagnostics: list[PlanningDiagnostic],
    relationships: list[PlanningRelationship],
    child_id: str,
    parent_id: str,
    source_path: Path,
) -> None:
    if child_id == parent_id:
        diagnostics.append(
            PlanningDiagnostic(
                artifact_id=child_id,
                path=source_path,
                severity="error",
                code="PLANNING_SELF_PARENT",
                message=(
                    f"planning artifact '{child_id}' cannot declare itself as parent"
                ),
            )
        )
        return

    parent = artifacts_by_id.get(parent_id)
    if parent is None or parent.kind != ARTIFACT_WORKSTREAM:
        diagnostics.append(
            PlanningDiagnostic(
                artifact_id=child_id,
                path=source_path,
                severity="error",
                code="PLANNING_UNKNOWN_PARENT_ID",
                message=f"parent_id references unknown planning parent '{parent_id}'",
            )
        )
        return
    relationships.append(
        PlanningRelationship(
            parent_id=parent_id,
            child_id=child_id,
            source_id=child_id,
            source_field=RELATION_PARENT_ID,
        )
    )


def _append_child_relationship(
    artifacts_by_id: dict[str, PlanningArtifact],
    diagnostics: list[PlanningDiagnostic],
    relationships: list[PlanningRelationship],
    parent_id: str,
    child_id: str,
    source_field: str,
    source_path: Path,
) -> None:
    if parent_id == child_id:
        diagnostics.append(
            PlanningDiagnostic(
                artifact_id=parent_id,
                path=source_path,
                severity="error",
                code="PLANNING_SELF_PARENT",
                message=(
                    f"planning artifact '{parent_id}' cannot list itself as a child"
                ),
            )
        )
        return

    child = artifacts_by_id.get(child_id)
    if child is None:
        diagnostics.append(
            PlanningDiagnostic(
                artifact_id=parent_id,
                path=source_path,
                severity="error",
                code="PLANNING_UNKNOWN_CHILD_ID",
                message=f"{source_field} references unknown child id '{child_id}'",
            )
        )
        return
    relationships.append(
        PlanningRelationship(
            parent_id=parent_id,
            child_id=child_id,
            source_id=parent_id,
            source_field=source_field,
        )
    )


def _append_work_item_relationship(
    artifacts_by_id: dict[str, PlanningArtifact],
    diagnostics: list[PlanningDiagnostic],
    relationships: list[PlanningRelationship],
    parent_id: str,
    child_id: str,
    source_path: Path,
) -> None:
    child = artifacts_by_id.get(child_id)
    if child is None:
        diagnostics.append(
            PlanningDiagnostic(
                artifact_id=parent_id,
                path=source_path,
                severity="error",
                code="PLANNING_UNKNOWN_CHILD_ID",
                message=f"work_items references unknown work item id '{child_id}'",
            )
        )
        return
    if child.kind != ARTIFACT_WORK_ITEM:
        diagnostics.append(
            PlanningDiagnostic(
                artifact_id=parent_id,
                path=source_path,
                severity="error",
                code="PLANNING_WORK_ITEM_CHILD_KIND_INVALID",
                message=(
                    f"work_items references non-work-item id '{child_id}' "
                    f"of kind '{child.kind}'"
                ),
            )
        )
        return
    relationships.append(
        PlanningRelationship(
            parent_id=parent_id,
            child_id=child_id,
            source_id=parent_id,
            source_field=RELATION_WORK_ITEMS,
        )
    )


def _children_by_parent(
    relationships: list[PlanningRelationship],
) -> dict[str, tuple[str, ...]]:
    children: dict[str, list[str]] = {}
    for relationship in relationships:
        child_ids = children.setdefault(relationship.parent_id, [])
        if relationship.child_id not in child_ids:
            child_ids.append(relationship.child_id)
    return {parent_id: tuple(child_ids) for parent_id, child_ids in children.items()}


def _parents_by_child(
    relationships: list[PlanningRelationship],
) -> dict[str, tuple[str, ...]]:
    parents: dict[str, list[str]] = {}
    for relationship in relationships:
        parent_ids = parents.setdefault(relationship.child_id, [])
        if relationship.parent_id not in parent_ids:
            parent_ids.append(relationship.parent_id)
    return {child_id: tuple(parent_ids) for child_id, parent_ids in parents.items()}


def _mark_active_leaves(
    artifacts_by_id: dict[str, PlanningArtifact],
    children_by_parent_id: dict[str, tuple[str, ...]],
) -> None:
    for artifact_id, artifact in tuple(artifacts_by_id.items()):
        if artifact.kind != ARTIFACT_WORK_ITEM:
            continue
        artifacts_by_id[artifact_id] = replace(
            artifact,
            is_active_leaf=artifact.status == "active"
            and not children_by_parent_id.get(artifact_id),
        )


def _detect_parent_child_mismatches(
    artifacts_by_id: dict[str, PlanningArtifact],
    diagnostics: list[PlanningDiagnostic],
    workstreams: tuple[Workstream, ...],
    work_items: tuple[WorkItem, ...],
    children_by_parent_id: dict[str, tuple[str, ...]],
    parents_by_child_id: dict[str, tuple[str, ...]],
) -> None:
    declared_parent_by_child = {
        workstream.id: workstream.parent_id
        for workstream in workstreams
        if workstream.parent_id
    }
    declared_parent_by_child.update(
        {
            work_item.id: work_item.parent_id
            for work_item in work_items
            if work_item.parent_id
        }
    )
    for child_id, declared_parent_id in declared_parent_by_child.items():
        for inferred_parent_id in parents_by_child_id.get(child_id, ()):
            if inferred_parent_id == declared_parent_id:
                continue
            parent = artifacts_by_id[inferred_parent_id]
            diagnostics.append(
                PlanningDiagnostic(
                    artifact_id=inferred_parent_id,
                    path=parent.path,
                    severity="warning",
                    code="PLANNING_PARENT_CHILD_MISMATCH",
                    message=(
                        f"child '{child_id}' declares parent_id '{declared_parent_id}' "
                        f"but is also listed under '{inferred_parent_id}'"
                    ),
                )
            )

    for child_id, parent_ids in parents_by_child_id.items():
        if len(parent_ids) <= 1:
            continue
        artifact = artifacts_by_id[child_id]
        diagnostics.append(
            PlanningDiagnostic(
                artifact_id=child_id,
                path=artifact.path,
                severity="warning",
                code="PLANNING_MULTIPLE_PARENTS",
                message=(
                    f"child '{child_id}' is related to multiple parents: "
                    f"{', '.join(parent_ids)}"
                ),
            )
        )


def _detect_active_state_gaps(
    artifacts_by_id: dict[str, PlanningArtifact],
    diagnostics: list[PlanningDiagnostic],
    workstreams: tuple[Workstream, ...],
    work_items: tuple[WorkItem, ...],
    children_by_parent_id: dict[str, tuple[str, ...]],
    parents_by_child_id: dict[str, tuple[str, ...]],
) -> None:
    active_work_item_ids = {
        work_item.id
        for work_item in work_items
        if work_item.status == "active" and work_item.id in artifacts_by_id
    }
    for work_item_id in sorted(active_work_item_ids):
        if parents_by_child_id.get(work_item_id):
            continue
        artifact = artifacts_by_id[work_item_id]
        diagnostics.append(
            PlanningDiagnostic(
                artifact_id=work_item_id,
                path=artifact.path,
                severity="warning",
                code="PLANNING_ORPHANED_ACTIVE_WORK_ITEM",
                message=(
                    f"active work item '{work_item_id}' is not attached to a "
                    "planning parent"
                ),
            )
        )

    active_workstream_ids = [
        workstream.id
        for workstream in workstreams
        if workstream.status == "active" and workstream.id in artifacts_by_id
    ]
    for workstream_id in sorted(active_workstream_ids):
        if _has_actionable_leaf(workstream_id, artifacts_by_id, children_by_parent_id):
            continue
        artifact = artifacts_by_id[workstream_id]
        diagnostics.append(
            PlanningDiagnostic(
                artifact_id=workstream_id,
                path=artifact.path,
                severity="warning",
                code="PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF",
                message=(
                    f"active workstream '{workstream_id}' has no active or "
                    "proposed work-item leaf"
                ),
            )
        )


def _has_actionable_leaf(
    workstream_id: str,
    artifacts_by_id: dict[str, PlanningArtifact],
    children_by_parent_id: dict[str, tuple[str, ...]],
) -> bool:
    visited: set[str] = set()
    stack = list(reversed(children_by_parent_id.get(workstream_id, ())))
    while stack:
        child_id = stack.pop()
        if child_id in visited:
            continue
        visited.add(child_id)
        child = artifacts_by_id.get(child_id)
        if child is None:
            continue
        if child.kind == ARTIFACT_WORK_ITEM and child.status in {"active", "proposed"}:
            return True
        if child.kind == ARTIFACT_WORKSTREAM:
            stack.extend(reversed(children_by_parent_id.get(child_id, ())))
    return False


def _find_workstream_cycles(
    artifacts_by_id: dict[str, PlanningArtifact],
    children_by_parent_id: dict[str, tuple[str, ...]],
) -> tuple[tuple[str, ...], ...]:
    cycles: list[tuple[str, ...]] = []
    seen_cycles: set[tuple[str, ...]] = set()
    visiting: list[str] = []
    visited: set[str] = set()

    def visit(workstream_id: str) -> None:
        if workstream_id in visiting:
            cycle = tuple(visiting[visiting.index(workstream_id) :])
            canonical = _canonical_cycle(cycle)
            if canonical not in seen_cycles:
                seen_cycles.add(canonical)
                cycles.append(cycle)
            return
        if workstream_id in visited:
            return
        visiting.append(workstream_id)
        for child_id in children_by_parent_id.get(workstream_id, ()):
            child = artifacts_by_id.get(child_id)
            if child is None or child.kind != ARTIFACT_WORKSTREAM:
                continue
            visit(child_id)
        visiting.pop()
        visited.add(workstream_id)

    for artifact_id, artifact in artifacts_by_id.items():
        if artifact.kind == ARTIFACT_WORKSTREAM:
            visit(artifact_id)

    return tuple(cycles)


def _canonical_cycle(cycle: tuple[str, ...]) -> tuple[str, ...]:
    rotations = [cycle[index:] + cycle[:index] for index in range(len(cycle))]
    return min(rotations)
