"""Semantic view models for future ``lrh serve`` dashboard surfaces.

This module intentionally provides typed, deterministic contracts rather than a
frontend implementation. The operational status vocabulary is dashboard-facing
and distinct from work-item lifecycle status values loaded from project-control
Markdown.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from lrh import core_state


class OperationalStatus(StrEnum):
    """Dashboard operational status, distinct from lifecycle status values."""

    NEEDS_ATTENTION = "needs_attention"
    ACTIVE_WORK = "active_work"
    AWAITING_REVIEW = "awaiting_review"
    STABLE = "stable"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


_OPERATIONAL_STATUS_LABELS = {
    OperationalStatus.NEEDS_ATTENTION: "Needs Attention",
    OperationalStatus.ACTIVE_WORK: "Active Work",
    OperationalStatus.AWAITING_REVIEW: "Awaiting Review",
    OperationalStatus.STABLE: "Stable",
    OperationalStatus.BLOCKED: "Blocked",
    OperationalStatus.UNKNOWN: "Unknown",
}

_OPERATIONAL_STATUS_DESCRIPTIONS = {
    OperationalStatus.NEEDS_ATTENTION: (
        "A project or item requires human review, repair, or decision."
    ),
    OperationalStatus.ACTIVE_WORK: (
        "Work is actively being planned, implemented, validated, or revised."
    ),
    OperationalStatus.AWAITING_REVIEW: (
        "Work is ready for human, CI, pull-request, or policy review."
    ),
    OperationalStatus.STABLE: (
        "Current state is validated or otherwise supported by known evidence."
    ),
    OperationalStatus.BLOCKED: (
        "Forward progress is stopped by a declared blocker or missing authority."
    ),
    OperationalStatus.UNKNOWN: (
        "LRH cannot establish the state from available control-plane data."
    ),
}

OPERATIONAL_LANE_ORDER = (
    OperationalStatus.NEEDS_ATTENTION,
    OperationalStatus.ACTIVE_WORK,
    OperationalStatus.AWAITING_REVIEW,
    OperationalStatus.STABLE,
    OperationalStatus.BLOCKED,
    OperationalStatus.UNKNOWN,
)

_REVIEW_STATUS_VALUES = frozenset(
    {
        "awaiting_review",
        "review",
        "in_review",
        "ready_for_review",
        "ready-for-review",
    }
)

_ACTIVE_STATUS_VALUES = frozenset(
    {
        "active",
        "in_progress",
        "in-progress",
        "implementing",
        "planned",
        "ready",
    }
)

_BLOCKED_STATUS_VALUES = frozenset({"blocked", "stalled"})


@dataclass(frozen=True)
class StatusBadgeView:
    """Human-facing badge metadata for an operational dashboard status."""

    status: OperationalStatus
    label: str
    description: str


@dataclass(frozen=True)
class EvidenceSummaryView:
    """Evidence availability summary without fabricated counts."""

    state: str = "unknown"
    passing_count: int | None = None
    total_count: int | None = None
    warnings_count: int | None = None
    failures_count: int | None = None
    last_validation_time: str | None = None

    @property
    def is_known(self) -> bool:
        """Return whether this summary carries available evidence data."""

        return self.state == "available"


@dataclass(frozen=True)
class ValidationSummaryView:
    """Small validation rollup for dashboard cards and inspectors."""

    state: str = "unknown"
    passing_count: int | None = None
    total_count: int | None = None
    warnings_count: int | None = None
    errors_count: int | None = None
    last_validation_time: str | None = None

    @property
    def has_errors(self) -> bool:
        """Return whether known validation data includes errors."""

        return self.errors_count is not None and self.errors_count > 0

    @property
    def has_warnings(self) -> bool:
        """Return whether known validation data includes warnings."""

        return self.warnings_count is not None and self.warnings_count > 0


@dataclass(frozen=True)
class OperationalStatusInputs:
    """Minimal facts used to derive a conservative operational status.

    The mapper only promotes a project to a concrete operational status when the
    corresponding input is explicit. Missing facts must remain ``None`` or
    ``False`` so the result falls back to ``unknown`` rather than overclaiming.
    """

    validation_error_count: int | None = None
    validation_warning_count: int | None = None
    blocker_count: int | None = None
    has_active_work: bool | None = None
    awaiting_review: bool | None = None
    steady: bool | None = None


@dataclass(frozen=True)
class ProjectSummaryView:
    """Dashboard-card summary for one project."""

    project_id: str
    name: str
    status: OperationalStatus
    status_badge: StatusBadgeView
    validation: ValidationSummaryView
    evidence: EvidenceSummaryView
    current_focus: str | None = None
    active_work_count: int | None = None
    source_path: str | None = None


@dataclass(frozen=True)
class OperationalLaneView:
    """Deterministic lane grouping for projects with the same status."""

    status: OperationalStatus
    label: str
    description: str
    projects: tuple[ProjectSummaryView, ...]

    @property
    def count(self) -> int:
        """Return the number of project cards in this lane."""

        return len(self.projects)


@dataclass(frozen=True)
class ProjectInspectorView:
    """Detail-ready project dashboard summary for future inspectors."""

    project: ProjectSummaryView
    diagnostics: tuple[str, ...] = ()
    source_links: tuple[str, ...] = ()


@dataclass(frozen=True)
class MetaDashboardView:
    """Top-level dashboard view grouped by operational status lanes."""

    lanes: tuple[OperationalLaneView, ...]
    total_projects: int


def status_label(status: OperationalStatus | str) -> str:
    """Return the human-facing label for an operational status value."""

    operational_status = coerce_operational_status(status)
    return _OPERATIONAL_STATUS_LABELS[operational_status]


def status_badge(status: OperationalStatus | str) -> StatusBadgeView:
    """Return badge metadata for an operational status value."""

    operational_status = coerce_operational_status(status)
    return StatusBadgeView(
        status=operational_status,
        label=_OPERATIONAL_STATUS_LABELS[operational_status],
        description=_OPERATIONAL_STATUS_DESCRIPTIONS[operational_status],
    )


def coerce_operational_status(status: OperationalStatus | str) -> OperationalStatus:
    """Coerce a status value, falling back to ``unknown`` for unsupported input."""

    if isinstance(status, OperationalStatus):
        return status
    try:
        return OperationalStatus(status)
    except ValueError:
        return OperationalStatus.UNKNOWN


def derive_operational_status(
    inputs: OperationalStatusInputs,
) -> OperationalStatus:
    """Derive a conservative dashboard status from currently known facts.

    Precedence is intentionally cautious: declared blockers stop progress;
    validation errors or warnings need attention; review-waiting and active-work
    signals are only used when explicit; stable requires an explicit steady
    signal plus known zero validation problems and no blockers. Missing or
    insufficient data returns ``unknown``.
    """

    if inputs.blocker_count is not None and inputs.blocker_count > 0:
        return OperationalStatus.BLOCKED
    if inputs.validation_error_count is not None and inputs.validation_error_count > 0:
        return OperationalStatus.NEEDS_ATTENTION
    if (
        inputs.validation_warning_count is not None
        and inputs.validation_warning_count > 0
    ):
        return OperationalStatus.NEEDS_ATTENTION
    if inputs.awaiting_review is True:
        return OperationalStatus.AWAITING_REVIEW
    if inputs.has_active_work is True:
        return OperationalStatus.ACTIVE_WORK
    if _has_explicit_stable_inputs(inputs):
        return OperationalStatus.STABLE
    return OperationalStatus.UNKNOWN


def validation_summary_from_core_state(
    state: core_state.CoreProjectState,
) -> ValidationSummaryView:
    """Build a validation dashboard summary from loaded core project state."""

    errors = state.validation.error_count
    warnings = state.validation.warning_count
    passing = 1 if state.validation.is_valid else 0
    return ValidationSummaryView(
        state="available",
        passing_count=passing,
        total_count=1,
        warnings_count=warnings,
        errors_count=errors,
    )


def evidence_summary_from_core_state(
    state: core_state.CoreProjectState,
) -> EvidenceSummaryView:
    """Build an evidence summary from explicit evidence links only."""

    if not state.evidence_links:
        return EvidenceSummaryView(state="unavailable")
    total = len(state.evidence_links)
    return EvidenceSummaryView(state="available", total_count=total)


def project_summary_from_core_state(
    state: core_state.CoreProjectState,
) -> ProjectSummaryView:
    """Build a project card summary from the first-tranche core state."""

    inputs = OperationalStatusInputs(
        validation_error_count=state.validation.error_count,
        validation_warning_count=state.validation.warning_count,
        blocker_count=_blocked_work_item_count(state),
        has_active_work=bool(state.active_leaf_work_items or state.workstreams),
        awaiting_review=_has_review_waiting_work(state),
        steady=_is_known_steady(state),
    )
    status = derive_operational_status(inputs)
    focus = state.current_focus.title if state.current_focus is not None else None
    return ProjectSummaryView(
        project_id=state.identity.project_name,
        name=state.identity.project_name,
        status=status,
        status_badge=status_badge(status),
        validation=validation_summary_from_core_state(state),
        evidence=evidence_summary_from_core_state(state),
        current_focus=focus,
        active_work_count=len(state.active_leaf_work_items),
        source_path=str(state.identity.project_dir),
    )


def build_meta_dashboard(
    projects: tuple[ProjectSummaryView, ...] | list[ProjectSummaryView],
) -> MetaDashboardView:
    """Group project summaries into stable operational swimlanes."""

    grouped: dict[OperationalStatus, list[ProjectSummaryView]] = {
        status: [] for status in OPERATIONAL_LANE_ORDER
    }
    for project in projects:
        grouped[project.status].append(project)

    lanes = []
    for status in OPERATIONAL_LANE_ORDER:
        sorted_projects = tuple(
            sorted(
                grouped[status],
                key=lambda project: (project.name.casefold(), project.project_id),
            )
        )
        lanes.append(
            OperationalLaneView(
                status=status,
                label=status_label(status),
                description=_OPERATIONAL_STATUS_DESCRIPTIONS[status],
                projects=sorted_projects,
            )
        )
    return MetaDashboardView(
        lanes=tuple(lanes),
        total_projects=sum(len(lane.projects) for lane in lanes),
    )


def _has_explicit_stable_inputs(inputs: OperationalStatusInputs) -> bool:
    return (
        inputs.steady is True
        and inputs.validation_error_count == 0
        and inputs.validation_warning_count == 0
        and (inputs.blocker_count is None or inputs.blocker_count == 0)
        and inputs.awaiting_review is not True
        and inputs.has_active_work is not True
    )


def _blocked_work_item_count(state: core_state.CoreProjectState) -> int:
    return sum(
        1
        for item in state.work_items
        if item.blocked_by or item.status.lower() in _BLOCKED_STATUS_VALUES
    )


def _has_review_waiting_work(state: core_state.CoreProjectState) -> bool:
    return any(
        item.status.lower() in _REVIEW_STATUS_VALUES for item in state.work_items
    )


def _is_known_steady(state: core_state.CoreProjectState) -> bool:
    has_control_state = state.current_focus is not None or bool(state.work_items)
    has_active_work = any(
        item.status.lower() in _ACTIVE_STATUS_VALUES for item in state.work_items
    )
    return state.validation.is_valid and has_control_state and not has_active_work
