"""Typed read-only view models for the LRH serve operational triage surface.

This module defines the deterministic, serializable contract that future
``lrh serve`` routes can render for operational swimlanes and capability gaps.
It projects already-computed state only; it does not load project files, browse
arbitrary paths, mutate repositories, dispatch agents, or reinterpret deeper
control-plane semantics outside the explicit fields supplied by callers.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Iterable, Mapping
from typing import Any, Literal

LaneId = Literal[
    "needs_attention",
    "needs_validation",
    "ready_for_prompted_work",
    "active_in_progress",
    "paused_blocked",
    "stable_complete",
    "unknown_unavailable",
]
CapabilityGapCategory = Literal[
    "unavailable",
    "not_implemented",
    "blocked",
    "unsafe_deferred",
    "unknown",
]
CapabilityGapSeverity = Literal["info", "warning", "error", "safety", "unknown"]
ActionKind = Literal["copy", "preview", "download", "open_source", "mutating"]
ValidationState = Literal[
    "valid", "warning", "error", "not_validated", "stale", "unknown"
]
ReadinessState = Literal["ready", "not_ready", "blocked", "unknown"]
SourceState = Literal["live", "cached", "unavailable", "unknown"]

LANE_ORDER: tuple[LaneId, ...] = (
    "needs_attention",
    "needs_validation",
    "ready_for_prompted_work",
    "active_in_progress",
    "paused_blocked",
    "stable_complete",
    "unknown_unavailable",
)

LANE_LABELS: Mapping[LaneId, str] = {
    "needs_attention": "Needs Attention",
    "needs_validation": "Needs Validation",
    "ready_for_prompted_work": "Ready for Prompted Work",
    "active_in_progress": "Active / In Progress",
    "paused_blocked": "Paused / Blocked",
    "stable_complete": "Stable / Complete",
    "unknown_unavailable": "Unknown / Unavailable",
}

LANE_EXPLANATIONS: Mapping[LaneId, str] = {
    "needs_attention": (
        "Validation errors, safety issues, missing authority, or other "
        "human-attention state is present."
    ),
    "needs_validation": (
        "Project state is available but has not been validated, validation is "
        "stale, or validation state is unknown."
    ),
    "ready_for_prompted_work": (
        "At least one leaf has enough readiness and prompt inputs for manual "
        "prompted work."
    ),
    "active_in_progress": (
        "Project state indicates active execution, in-progress work items, or "
        "open manual run state."
    ),
    "paused_blocked": (
        "Explicit blockers, pauses, or missing upstream decisions prevent safe "
        "progression."
    ),
    "stable_complete": (
        "No active actionable leaves are known, and validation/source state is "
        "healthy enough to display."
    ),
    "unknown_unavailable": (
        "Project source, registry entry, or required state cannot be resolved."
    ),
}


@dataclasses.dataclass(frozen=True)
class SourceLink:
    """Deterministic link to a project-control or LRH-owned source."""

    label: str
    href: str
    source_type: str = "source"

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable projection."""

        return _to_jsonable(dataclasses.asdict(self))


@dataclasses.dataclass(frozen=True)
class ValidationBadge:
    """Small validation projection for cards and lane classification."""

    status: ValidationState
    error_count: int = 0
    warning_count: int = 0
    stale: bool = False
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable projection."""

        return _to_jsonable(dataclasses.asdict(self))


@dataclasses.dataclass(frozen=True)
class ReadinessBadge:
    """Small readiness projection for prompted-work affordances."""

    status: ReadinessState
    ready_leaf_count: int = 0
    deficient_leaf_count: int = 0
    blocker_count: int = 0
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable projection."""

        return _to_jsonable(dataclasses.asdict(self))


@dataclasses.dataclass(frozen=True)
class CapabilityGap:
    """First-class safe-default state for missing or deferred capabilities."""

    category: CapabilityGapCategory
    label: str
    explanation: str
    severity: CapabilityGapSeverity = "info"
    source_links: tuple[SourceLink, ...] = ()
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable projection."""

        return _to_jsonable(dataclasses.asdict(self))


@dataclasses.dataclass(frozen=True)
class ActionAffordance:
    """Read-only UI affordance metadata for future buttons and links."""

    id: str
    label: str
    action: ActionKind
    enabled: bool
    mutates_repository: bool = False
    disabled_reason: str | None = None
    href: str | None = None
    source_links: tuple[SourceLink, ...] = ()

    def __post_init__(self) -> None:
        """Enforce safe-default action contracts for the MVP."""

        if not self.enabled and not self.disabled_reason:
            raise ValueError("disabled action affordances require a disabled_reason")
        if self.enabled and self.disabled_reason:
            raise ValueError("enabled action affordances must not set disabled_reason")
        if self.enabled and self.mutates_repository:
            raise ValueError("repository-mutating actions must not be enabled")

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable projection."""

        return _to_jsonable(dataclasses.asdict(self))


@dataclasses.dataclass(frozen=True)
class ProjectOperationalCard:
    """Card-level projection for one project in operational swimlanes."""

    project_id: str
    display_name: str
    short_name: str
    locator: str
    source_state: SourceState
    validation: ValidationBadge
    readiness: ReadinessBadge
    current_focus_summary: str | None = None
    active_workstream_count: int = 0
    active_work_item_count: int = 0
    in_progress_work_item_count: int = 0
    active_execution_count: int = 0
    readiness_deficient_leaf_count: int = 0
    adopted_not_implemented_design_count: int = 0
    blocker_count: int = 0
    paused: bool = False
    missing_authority: bool = False
    safety_issue_count: int = 0
    capability_gaps: tuple[CapabilityGap, ...] = ()
    source_links: tuple[SourceLink, ...] = ()
    detail_url: str | None = None
    lane_id: LaneId | None = None
    lane_rationale: tuple[str, ...] = ()
    lane_evidence: tuple[str, ...] = ()

    def classified(self) -> ProjectOperationalCard:
        """Return this card with deterministic lane fields populated."""

        assignment = classify_project_card(self)
        return dataclasses.replace(
            self,
            lane_id=assignment.lane_id,
            lane_rationale=assignment.rationale,
            lane_evidence=assignment.evidence,
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable projection with lane fields populated."""

        card = self if self.lane_id is not None else self.classified()
        return _to_jsonable(dataclasses.asdict(card))


@dataclasses.dataclass(frozen=True)
class ProjectOperationalDetail:
    """Detail-page contract stub for a single project's operational state."""

    project_card: ProjectOperationalCard
    validation: ValidationBadge
    readiness: ReadinessBadge
    focus: Mapping[str, object] | None = None
    designs: tuple[Mapping[str, object], ...] = ()
    workstreams: tuple[Mapping[str, object], ...] = ()
    work_items: tuple[Mapping[str, object], ...] = ()
    ready_leaves: tuple[Mapping[str, object], ...] = ()
    not_ready_leaves: tuple[Mapping[str, object], ...] = ()
    prompt_affordances: tuple[ActionAffordance, ...] = ()
    capability_gaps: tuple[CapabilityGap, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable projection."""

        return _to_jsonable(dataclasses.asdict(self))


@dataclasses.dataclass(frozen=True)
class LaneAssignment:
    """Deterministic lane-classification result for one projected card."""

    lane_id: LaneId
    rationale: tuple[str, ...]
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable projection."""

        return _to_jsonable(dataclasses.asdict(self))


@dataclasses.dataclass(frozen=True)
class OperationalLane:
    """Operational swimlane summary with deterministic project membership."""

    id: LaneId
    label: str
    explanation: str
    project_count: int
    project_ids: tuple[str, ...]
    evidence_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable projection."""

        return _to_jsonable(dataclasses.asdict(self))


@dataclasses.dataclass(frozen=True)
class ServeWorkspaceView:
    """Top-level typed projection for a serve operational-triage workspace."""

    generated_at: str | None
    workspace_mode: str
    projects: tuple[ProjectOperationalCard, ...]
    lanes: tuple[OperationalLane, ...]
    capability_gaps: tuple[CapabilityGap, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable projection."""

        return _to_jsonable(dataclasses.asdict(self))


def classify_project_card(card: ProjectOperationalCard) -> LaneAssignment:
    """Classify an already-projected card into one deterministic lane.

    The classifier uses only explicit fields on ``card``. It never loads files,
    resolves locators, dispatches agents, or mutates repository state.
    """

    evidence = _card_evidence(card)
    validation = card.validation
    readiness = card.readiness
    if card.source_state in {"unavailable", "unknown"} or _has_gap(
        card, {"unavailable", "unknown"}
    ):
        return LaneAssignment(
            lane_id="unknown_unavailable",
            rationale=_unknown_unavailable_rationale(card),
            evidence=evidence,
        )
    if (
        validation.status == "error"
        or validation.error_count > 0
        or card.safety_issue_count > 0
        or card.missing_authority
        or _has_gap(card, {"unsafe_deferred"})
    ):
        return LaneAssignment(
            lane_id="needs_attention",
            rationale=_attention_rationale(card),
            evidence=evidence,
        )
    if (
        card.paused
        or card.blocker_count > 0
        or readiness.status == "blocked"
        or readiness.blocker_count > 0
        or _has_gap(card, {"blocked"})
    ):
        return LaneAssignment(
            lane_id="paused_blocked",
            rationale=_blocked_rationale(card),
            evidence=evidence,
        )
    if validation.status in {"not_validated", "stale", "unknown"} or validation.stale:
        return LaneAssignment(
            lane_id="needs_validation",
            rationale=_validation_rationale(card),
            evidence=evidence,
        )
    if card.active_execution_count > 0 or card.in_progress_work_item_count > 0:
        return LaneAssignment(
            lane_id="active_in_progress",
            rationale=_active_rationale(card),
            evidence=evidence,
        )
    if card.readiness.ready_leaf_count > 0:
        return LaneAssignment(
            lane_id="ready_for_prompted_work",
            rationale=(f"ready_leaf_count is {card.readiness.ready_leaf_count}",),
            evidence=evidence,
        )
    if validation.status in {"valid", "warning"} and card.source_state in {
        "live",
        "cached",
    }:
        return LaneAssignment(
            lane_id="stable_complete",
            rationale=(
                "validation/source state is displayable and no actionable "
                "leaves are ready",
            ),
            evidence=evidence,
        )
    return LaneAssignment(
        lane_id="unknown_unavailable",
        rationale=("card fields did not match a known operational state",),
        evidence=evidence,
    )


def build_workspace_view(
    *,
    workspace_mode: str,
    projects: Iterable[ProjectOperationalCard],
    capability_gaps: Iterable[CapabilityGap] = (),
    generated_at: str | None = None,
) -> ServeWorkspaceView:
    """Build a stable top-level workspace projection from projected cards."""

    classified_projects = tuple(
        card.classified()
        for card in sorted(
            projects, key=lambda item: (item.display_name, item.project_id)
        )
    )
    lanes = tuple(_build_lane(lane_id, classified_projects) for lane_id in LANE_ORDER)
    sorted_gaps = tuple(
        sorted(
            capability_gaps,
            key=lambda gap: (gap.category, gap.severity, gap.label, gap.explanation),
        )
    )
    return ServeWorkspaceView(
        generated_at=generated_at,
        workspace_mode=workspace_mode,
        projects=classified_projects,
        lanes=lanes,
        capability_gaps=sorted_gaps,
    )


def default_capability_gap_for_unimplemented(
    label: str, explanation: str
) -> CapabilityGap:
    """Return the standard non-error projection for planned unbuilt features."""

    return CapabilityGap(
        category="not_implemented",
        label=label,
        explanation=explanation,
        severity="info",
    )


def _build_lane(
    lane_id: LaneId,
    projects: tuple[ProjectOperationalCard, ...],
) -> OperationalLane:
    project_ids = tuple(card.project_id for card in projects if card.lane_id == lane_id)
    evidence_refs = tuple(
        sorted(
            {
                evidence
                for card in projects
                if card.lane_id == lane_id
                for evidence in card.lane_evidence
            }
        )
    )
    return OperationalLane(
        id=lane_id,
        label=LANE_LABELS[lane_id],
        explanation=LANE_EXPLANATIONS[lane_id],
        project_count=len(project_ids),
        project_ids=project_ids,
        evidence_refs=evidence_refs,
    )


def _unknown_unavailable_rationale(card: ProjectOperationalCard) -> tuple[str, ...]:
    reasons = []
    if card.source_state in {"unavailable", "unknown"}:
        reasons.append(f"source_state is {card.source_state}")
    if _has_gap(card, {"unavailable"}):
        reasons.append("unavailable capability gap is present")
    if _has_gap(card, {"unknown"}):
        reasons.append("unknown capability gap is present")
    return tuple(reasons) or ("required state cannot be resolved",)


def _attention_rationale(card: ProjectOperationalCard) -> tuple[str, ...]:
    reasons = []
    if card.validation.status == "error":
        reasons.append("validation status is error")
    if card.validation.error_count > 0:
        reasons.append(f"validation error_count is {card.validation.error_count}")
    if card.safety_issue_count > 0:
        reasons.append(f"safety_issue_count is {card.safety_issue_count}")
    if card.missing_authority:
        reasons.append("missing authority is present")
    if _has_gap(card, {"unsafe_deferred"}):
        reasons.append("unsafe-deferred capability gap is present")
    return tuple(reasons) or ("human-attention field is present",)


def _blocked_rationale(card: ProjectOperationalCard) -> tuple[str, ...]:
    reasons = []
    if card.paused:
        reasons.append("paused is true")
    if card.blocker_count > 0:
        reasons.append(f"blocker_count is {card.blocker_count}")
    if card.readiness.status == "blocked":
        reasons.append("readiness status is blocked")
    if card.readiness.blocker_count > 0:
        reasons.append(f"readiness blocker_count is {card.readiness.blocker_count}")
    if _has_gap(card, {"blocked"}):
        reasons.append("blocked capability gap is present")
    return tuple(reasons) or ("blocked field is present",)


def _validation_rationale(card: ProjectOperationalCard) -> tuple[str, ...]:
    if card.validation.stale:
        return ("validation stale flag is true",)
    return (f"validation status is {card.validation.status}",)


def _active_rationale(card: ProjectOperationalCard) -> tuple[str, ...]:
    reasons = []
    if card.active_execution_count > 0:
        reasons.append(f"active_execution_count is {card.active_execution_count}")
    if card.in_progress_work_item_count > 0:
        reasons.append(
            f"in_progress_work_item_count is {card.in_progress_work_item_count}"
        )
    return tuple(reasons) or ("active execution state is present",)


def _card_evidence(card: ProjectOperationalCard) -> tuple[str, ...]:
    evidence = [
        *card.validation.evidence,
        *card.readiness.evidence,
        *(evidence for gap in card.capability_gaps for evidence in gap.evidence),
    ]
    return tuple(sorted(set(evidence)))


def _has_gap(
    card: ProjectOperationalCard,
    categories: set[CapabilityGapCategory],
) -> bool:
    return any(gap.category in categories for gap in card.capability_gaps)


def _to_jsonable(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return _to_jsonable(dataclasses.asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_to_jsonable(item) for item in value]
    return value
