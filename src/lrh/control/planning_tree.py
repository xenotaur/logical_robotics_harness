"""Relationship index for workstreams and work-item planning leaves."""

from __future__ import annotations

from dataclasses import dataclass
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
    _detect_parent_child_mismatches(
        artifacts_by_id,
        diagnostics,
        workstreams,
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
        artifacts_by_id[artifact.id] = PlanningArtifact(
            id=artifact.id,
            kind=artifact_kind,
            path=artifact.path,
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
            _append_child_relationship(
                artifacts_by_id,
                diagnostics,
                relationships,
                workstream.id,
                child_id,
                RELATION_WORK_ITEMS,
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


def _detect_parent_child_mismatches(
    artifacts_by_id: dict[str, PlanningArtifact],
    diagnostics: list[PlanningDiagnostic],
    workstreams: tuple[Workstream, ...],
    children_by_parent_id: dict[str, tuple[str, ...]],
    parents_by_child_id: dict[str, tuple[str, ...]],
) -> None:
    declared_parent_by_child = {
        workstream.id: workstream.parent_id
        for workstream in workstreams
        if workstream.parent_id
    }
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

    for parent_id, child_ids in children_by_parent_id.items():
        for child_id in child_ids:
            parent_ids = parents_by_child_id.get(child_id, ())
            if len(parent_ids) <= 1:
                continue
            artifact = artifacts_by_id[parent_id]
            diagnostics.append(
                PlanningDiagnostic(
                    artifact_id=parent_id,
                    path=artifact.path,
                    severity="warning",
                    code="PLANNING_MULTIPLE_PARENTS",
                    message=(
                        f"child '{child_id}' is related to multiple parents: "
                        f"{', '.join(parent_ids)}"
                    ),
                )
            )


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
