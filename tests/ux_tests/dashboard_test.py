"""Tests for future dashboard UX support contracts."""

from __future__ import annotations

import unittest

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
            "Stable",
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


if __name__ == "__main__":
    unittest.main()
