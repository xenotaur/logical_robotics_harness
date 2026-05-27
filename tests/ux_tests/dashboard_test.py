"""Tests for future dashboard UX support contracts."""

from __future__ import annotations

import pathlib
import unittest

from lrh import core_state
from lrh.meta import workspace as meta_workspace
from lrh.ux import dashboard


class OperationalStatusTest(unittest.TestCase):
    def test_status_values_and_labels_are_human_facing(self) -> None:
        self.assertEqual(
            dashboard.OperationalStatus.NEEDS_ATTENTION.value,
            "needs_attention",
        )
        self.assertEqual(
            dashboard.status_label(dashboard.OperationalStatus.NEEDS_ATTENTION),
            "Needs Attention",
        )
        self.assertEqual(
            dashboard.status_label(dashboard.OperationalStatus.ACTIVE_WORK),
            "Active Work",
        )
        self.assertEqual(
            dashboard.status_label(dashboard.OperationalStatus.AWAITING_REVIEW),
            "Awaiting Review",
        )
        self.assertEqual(
            dashboard.status_label(dashboard.OperationalStatus.STABLE),
            "Stable / No Action Needed",
        )
        self.assertEqual(
            dashboard.status_label(dashboard.OperationalStatus.BLOCKED),
            "Blocked",
        )
        self.assertEqual(
            dashboard.status_label(dashboard.OperationalStatus.UNKNOWN),
            "Unknown",
        )

    def test_unknown_status_fallback_is_conservative(self) -> None:
        self.assertEqual(
            dashboard.coerce_operational_status("unexpected-lifecycle-status"),
            dashboard.OperationalStatus.UNKNOWN,
        )
        self.assertEqual(
            dashboard.status_badge("unexpected-lifecycle-status").label,
            "Unknown",
        )
        self.assertEqual(
            dashboard.coerce_operational_status(None),
            dashboard.OperationalStatus.UNKNOWN,
        )
        self.assertEqual(
            dashboard.coerce_operational_status(123),
            dashboard.OperationalStatus.UNKNOWN,
        )


class OperationalStatusMapperTest(unittest.TestCase):
    def test_mapper_returns_unknown_for_insufficient_data(self) -> None:
        status = dashboard.derive_operational_status(
            dashboard.OperationalStatusInputs()
        )

        self.assertEqual(status, dashboard.OperationalStatus.UNKNOWN)

    def test_mapper_prioritizes_blockers_and_validation_findings(self) -> None:
        blocked = dashboard.derive_operational_status(
            dashboard.OperationalStatusInputs(
                blocker_count=1,
                validation_error_count=0,
                has_active_work=True,
            )
        )
        needs_attention = dashboard.derive_operational_status(
            dashboard.OperationalStatusInputs(
                validation_error_count=1,
                blocker_count=0,
                has_active_work=True,
            )
        )
        warning_attention = dashboard.derive_operational_status(
            dashboard.OperationalStatusInputs(
                validation_error_count=0,
                validation_warning_count=1,
            )
        )

        self.assertEqual(blocked, dashboard.OperationalStatus.BLOCKED)
        self.assertEqual(
            needs_attention,
            dashboard.OperationalStatus.NEEDS_ATTENTION,
        )
        self.assertEqual(
            warning_attention,
            dashboard.OperationalStatus.NEEDS_ATTENTION,
        )

    def test_mapper_uses_explicit_review_active_and_stable_signals(self) -> None:
        awaiting_review = dashboard.derive_operational_status(
            dashboard.OperationalStatusInputs(awaiting_review=True)
        )
        active = dashboard.derive_operational_status(
            dashboard.OperationalStatusInputs(has_active_work=True)
        )
        stable = dashboard.derive_operational_status(
            dashboard.OperationalStatusInputs(
                validation_error_count=0,
                validation_warning_count=0,
                blocker_count=0,
                steady=True,
            )
        )

        self.assertEqual(
            awaiting_review,
            dashboard.OperationalStatus.AWAITING_REVIEW,
        )
        self.assertEqual(active, dashboard.OperationalStatus.ACTIVE_WORK)
        self.assertEqual(stable, dashboard.OperationalStatus.STABLE)


class MetaDashboardViewTest(unittest.TestCase):
    def test_lane_grouping_is_deterministic_and_stable(self) -> None:
        projects = [
            _project("zeta", dashboard.OperationalStatus.UNKNOWN),
            _project("alpha", dashboard.OperationalStatus.ACTIVE_WORK),
            _project("beta", dashboard.OperationalStatus.ACTIVE_WORK),
            _project("repair", dashboard.OperationalStatus.NEEDS_ATTENTION),
        ]

        view = dashboard.build_meta_dashboard(projects)

        self.assertEqual(view.total_projects, 4)
        self.assertEqual(
            [lane.status for lane in view.lanes],
            list(dashboard.OPERATIONAL_LANE_ORDER),
        )
        self.assertEqual(view.lanes[0].label, "Needs Attention")
        self.assertEqual(
            [project.name for project in view.lanes[1].projects],
            ["alpha", "beta"],
        )
        self.assertEqual(view.lanes[1].count, 2)
        self.assertEqual(view.lanes[-1].projects[0].name, "zeta")

    def test_project_operational_card_uses_warning_and_workstream_counts(self) -> None:
        warned = dashboard.project_operational_card_from_record(
            _record("warned"),
            source_state="live",
            validation_status="valid",
            validation_error_count=0,
            validation_warning_count=1,
            active_work_item_count=0,
        )
        active_stream = dashboard.project_operational_card_from_record(
            _record("stream"),
            source_state="live",
            validation_status="valid",
            validation_error_count=0,
            validation_warning_count=0,
            active_workstream_count=1,
            active_work_item_count=0,
        )

        self.assertEqual(warned.status, dashboard.OperationalStatus.NEEDS_ATTENTION)
        self.assertEqual(active_stream.status, dashboard.OperationalStatus.ACTIVE_WORK)

    def test_project_operational_card_uses_blocked_review_and_steady_inputs(
        self,
    ) -> None:
        blocked = dashboard.project_operational_card_from_record(
            _record("blocked"),
            source_state="live",
            validation_error_count=0,
            validation_warning_count=0,
            blocker_count=1,
            active_work_item_count=1,
        )
        review = dashboard.project_operational_card_from_record(
            _record("review"),
            source_state="live",
            validation_error_count=0,
            validation_warning_count=0,
            awaiting_review=True,
            active_work_item_count=1,
        )
        stable = dashboard.project_operational_card_from_record(
            _record("stable"),
            source_state="live",
            validation_error_count=0,
            validation_warning_count=0,
            active_workstream_count=0,
            active_work_item_count=0,
            steady=True,
        )

        self.assertEqual(blocked.status, dashboard.OperationalStatus.BLOCKED)
        self.assertEqual(review.status, dashboard.OperationalStatus.AWAITING_REVIEW)
        self.assertEqual(stable.status, dashboard.OperationalStatus.STABLE)

    def test_project_operational_card_semantic_fields_match_legacy_aliases(
        self,
    ) -> None:
        card = dashboard.project_operational_card_from_record(
            _record("semantic"),
            source_state="live",
            validation_status="error",
            validation_error_count=2,
            validation_warning_count=1,
            capability_gaps=(
                dashboard.CapabilityGapView(
                    field="source_state",
                    state="unknown",
                    message="Source state is unknown.",
                ),
            ),
            diagnostics=("example diagnostic",),
            validation_diagnostics=("missing metadata",),
            validation_next_action="Run: lrh validate",
        )

        self.assertEqual(card.project_source_access, card.source_state)
        self.assertEqual(
            card.control_plane_validation["status"],
            card.validation_status,
        )
        self.assertEqual(card.triage_lane, card.lane)
        self.assertEqual(card.lrh_capability_gaps, card.capability_gaps)
        self.assertEqual(card.other_diagnostics, card.diagnostics)


class EvidenceSummaryViewTest(unittest.TestCase):
    def test_unknown_and_unavailable_evidence_are_explicit(self) -> None:
        unknown = dashboard.EvidenceSummaryView()
        unavailable = dashboard.EvidenceSummaryView(state="unavailable")

        self.assertEqual(unknown.state, "unknown")
        self.assertIsNone(unknown.total_count)
        self.assertFalse(unknown.is_known)
        self.assertEqual(unavailable.state, "unavailable")
        self.assertFalse(unavailable.is_known)

    def test_available_evidence_counts_are_preserved(self) -> None:
        evidence = dashboard.EvidenceSummaryView(
            state="available",
            passing_count=3,
            total_count=4,
            warnings_count=1,
            failures_count=0,
            last_validation_time="2026-05-16T00:14:00-04:00",
        )

        self.assertTrue(evidence.is_known)
        self.assertEqual(evidence.passing_count, 3)
        self.assertEqual(evidence.total_count, 4)
        self.assertEqual(evidence.warnings_count, 1)
        self.assertEqual(evidence.failures_count, 0)
        self.assertEqual(
            evidence.last_validation_time,
            "2026-05-16T00:14:00-04:00",
        )


class CoreStateAdapterTest(unittest.TestCase):
    def test_validation_summary_preserves_known_diagnostics_without_fake_totals(
        self,
    ) -> None:
        state = _core_state(
            validation=core_state.ValidationSummary(
                is_valid=False,
                error_count=3,
                warning_count=2,
                diagnostics=(),
            )
        )

        summary = dashboard.validation_summary_from_core_state(state)

        self.assertEqual(summary.state, "available")
        self.assertIsNone(summary.passing_count)
        self.assertIsNone(summary.total_count)
        self.assertEqual(summary.errors_count, 3)
        self.assertEqual(summary.warnings_count, 2)
        self.assertTrue(summary.has_errors)
        self.assertTrue(summary.has_warnings)

    def test_evidence_summary_uses_explicit_links_only(self) -> None:
        unavailable = dashboard.evidence_summary_from_core_state(_core_state())
        available = dashboard.evidence_summary_from_core_state(
            _core_state(
                evidence_links=(
                    core_state.EvidenceLink(
                        source_id="WI-1",
                        source_kind="work_item",
                        field="evidence",
                        target="project/evidence/run.md",
                    ),
                )
            )
        )

        self.assertEqual(unavailable.state, "unavailable")
        self.assertFalse(unavailable.is_known)
        self.assertEqual(available.state, "available")
        self.assertEqual(available.total_count, 1)
        self.assertTrue(available.is_known)

    def test_project_summary_does_not_treat_archived_workstream_as_active(
        self,
    ) -> None:
        state = _core_state(
            project_root=pathlib.Path("/workspace/projects/duplicate"),
            project_name="duplicate",
            current_focus=_focus(),
            workstreams=(
                _workstream(
                    workstream_id="WS-DONE",
                    status="archived",
                ),
            ),
        )

        summary = dashboard.project_summary_from_core_state(state)

        self.assertEqual(summary.project_id, "/workspace/projects/duplicate")
        self.assertEqual(summary.name, "duplicate")
        self.assertEqual(summary.status, dashboard.OperationalStatus.STABLE)
        self.assertEqual(summary.current_focus, "Current Focus")
        self.assertEqual(summary.active_work_count, 0)

    def test_project_summary_uses_active_workstream_as_active_signal(self) -> None:
        state = _core_state(
            current_focus=_focus(),
            workstreams=(_workstream(status="active"),),
        )

        summary = dashboard.project_summary_from_core_state(state)

        self.assertEqual(summary.status, dashboard.OperationalStatus.ACTIVE_WORK)

    def test_project_summary_counts_blockers_before_active_work(self) -> None:
        blocked_item = _work_item(
            work_item_id="WI-BLOCKED",
            status="active",
            blocked_by=("external-dependency",),
            is_active_leaf=True,
        )
        state = _core_state(
            current_focus=_focus(),
            work_items=(blocked_item,),
            active_leaf_work_items=(blocked_item,),
        )

        summary = dashboard.project_summary_from_core_state(state)

        self.assertEqual(summary.status, dashboard.OperationalStatus.BLOCKED)
        self.assertEqual(summary.active_work_count, 1)


def _record(name: str) -> meta_workspace.MetaProjectRecord:
    return meta_workspace.MetaProjectRecord(
        registry_name=name,
        short_name=name,
        display_name=name.title(),
        project_id=f"proj-{name}",
        repo_locator=f"repos/{name}",
        project_dir="project",
        setup_state="unknown",
    )


def _project(
    name: str,
    status: dashboard.OperationalStatus,
) -> dashboard.ProjectSummaryView:
    return dashboard.ProjectSummaryView(
        project_id=name,
        name=name,
        status=status,
        status_badge=dashboard.status_badge(status),
        validation=dashboard.ValidationSummaryView(),
        evidence=dashboard.EvidenceSummaryView(),
    )


def _core_state(
    *,
    project_root: pathlib.Path = pathlib.Path("/workspace/projects/example"),
    project_name: str = "example",
    validation: core_state.ValidationSummary | None = None,
    current_focus: core_state.FocusState | None = None,
    workstreams: tuple[core_state.WorkstreamState, ...] = (),
    work_items: tuple[core_state.WorkItemState, ...] = (),
    active_leaf_work_items: tuple[core_state.WorkItemState, ...] = (),
    evidence_links: tuple[core_state.EvidenceLink, ...] = (),
) -> core_state.CoreProjectState:
    project_dir = project_root / "project"
    return core_state.CoreProjectState(
        identity=core_state.ProjectIdentity(
            project_root=project_root,
            project_dir=project_dir,
            project_name=project_name,
        ),
        validation=validation
        or core_state.ValidationSummary(
            is_valid=True,
            error_count=0,
            warning_count=0,
            diagnostics=(),
        ),
        planning=core_state.PlanningState(
            relationships=(),
            diagnostics=(),
            cycles=(),
            active_leaf_ids=tuple(item.id for item in active_leaf_work_items),
            status_counts_by_kind={},
        ),
        current_focus=current_focus,
        workstreams=workstreams,
        work_items=work_items,
        active_leaf_work_items=active_leaf_work_items,
        evidence_links=evidence_links,
        prompt_inputs=core_state.PromptRenderingInputs(
            project_name=project_name,
            current_focus_id=current_focus.id if current_focus else None,
            current_focus_title=current_focus.title if current_focus else None,
            active_leaf_work_item_ids=tuple(item.id for item in active_leaf_work_items),
            active_workstream_ids=tuple(
                workstream.id
                for workstream in workstreams
                if workstream.status == "active"
            ),
            validation_is_valid=True,
        ),
        work_items_by_id={item.id: item for item in work_items},
        workstreams_by_id={workstream.id: workstream for workstream in workstreams},
    )


def _focus() -> core_state.FocusState:
    return core_state.FocusState(
        id="FOCUS-1",
        title="Current Focus",
        status="active",
        priority=None,
        owner=None,
        path=pathlib.Path("project/focus/current_focus.md"),
        related_principles=(),
        frontmatter_keys=(),
    )


def _workstream(
    *,
    workstream_id: str = "WS-1",
    status: str = "active",
) -> core_state.WorkstreamState:
    return core_state.WorkstreamState(
        id=workstream_id,
        title="Workstream",
        status=status,
        stage="implementation",
        bucket=None,
        path=pathlib.Path(f"project/workstreams/{workstream_id}.md"),
        parent_ids=(),
        child_ids=(),
        related_focus=(),
        related_roadmap=(),
        related_design=(),
        work_items=(),
        evidence=(),
        frontmatter_keys=(),
    )


def _work_item(
    *,
    work_item_id: str = "WI-1",
    status: str = "active",
    blocked_by: tuple[str, ...] = (),
    is_active_leaf: bool = False,
) -> core_state.WorkItemState:
    return core_state.WorkItemState(
        id=work_item_id,
        title="Work Item",
        type="deliverable",
        status=status,
        priority=None,
        owner=None,
        path=pathlib.Path(f"project/work_items/{work_item_id}.md"),
        parent_ids=(),
        child_ids=(),
        related_focus=(),
        related_roadmap=(),
        related_workstreams=(),
        related_design=(),
        depends_on=(),
        blocked_by=blocked_by,
        required_evidence=(),
        artifacts_expected=(),
        execution_readiness=None,
        is_current_focus_related=False,
        is_active_leaf=is_active_leaf,
        frontmatter_keys=(),
    )


if __name__ == "__main__":
    unittest.main()
