"""Tests for serve operational triage view models."""

from __future__ import annotations

import json
import unittest

from lrh import serve_triage


class ServeTriageTest(unittest.TestCase):
    """Cover deterministic lane, capability-gap, and action projections."""

    def test_representative_cards_classify_into_deterministic_lanes(self) -> None:
        cards = [
            _card("unknown", source_state="unavailable"),
            _card("attention", validation=serve_triage.ValidationBadge("error", 1)),
            _card("validation", validation=serve_triage.ValidationBadge("stale")),
            _card(
                "ready",
                readiness=serve_triage.ReadinessBadge("ready", ready_leaf_count=2),
            ),
            _card("active", in_progress_work_item_count=1),
            _card("blocked", blocker_count=1),
            _card("stable"),
        ]

        assignments = {
            card.project_id: serve_triage.classify_project_card(card) for card in cards
        }

        self.assertEqual(assignments["attention"].lane_id, "needs_attention")
        self.assertIn("validation status is error", assignments["attention"].rationale)
        self.assertIn("validation error_count is 1", assignments["attention"].rationale)
        self.assertEqual(assignments["validation"].lane_id, "needs_validation")
        self.assertEqual(assignments["ready"].lane_id, "ready_for_prompted_work")
        self.assertEqual(assignments["active"].lane_id, "active_in_progress")
        self.assertEqual(assignments["blocked"].lane_id, "paused_blocked")
        self.assertEqual(assignments["stable"].lane_id, "stable_complete")
        self.assertEqual(assignments["unknown"].lane_id, "unknown_unavailable")

    def test_error_status_without_error_count_has_clear_rationale(self) -> None:
        assignment = serve_triage.classify_project_card(
            _card("status-only-error", validation=serve_triage.ValidationBadge("error"))
        )

        self.assertEqual(assignment.lane_id, "needs_attention")
        self.assertEqual(assignment.rationale, ("validation status is error",))

    def test_blocked_status_without_blocker_count_has_clear_rationale(self) -> None:
        assignment = serve_triage.classify_project_card(
            _card(
                "status-only-blocked", readiness=serve_triage.ReadinessBadge("blocked")
            )
        )

        self.assertEqual(assignment.lane_id, "paused_blocked")
        self.assertEqual(assignment.rationale, ("readiness status is blocked",))

    def test_unavailable_capability_gap_classifies_unknown_unavailable(self) -> None:
        card = _card(
            "source-gap",
            capability_gaps=(
                serve_triage.CapabilityGap(
                    category="unavailable",
                    label="Project source unavailable",
                    explanation="The registered source could not be resolved.",
                    severity="warning",
                ),
            ),
        )

        assignment = serve_triage.classify_project_card(card)

        self.assertEqual(assignment.lane_id, "unknown_unavailable")
        self.assertIn("unavailable capability gap is present", assignment.rationale)

    def test_capability_gap_projection_is_json_serializable(self) -> None:
        gap = serve_triage.CapabilityGap(
            category="not_implemented",
            label="Meta swimlane page",
            explanation=(
                "The design exists, but the route is intentionally future work."
            ),
            severity="info",
            source_links=(
                serve_triage.SourceLink(
                    label="proposal",
                    href="project/design/proposals/proposed/lrh-serve-operational-triage-mvp/00_proposal.md",
                    source_type="design",
                ),
            ),
            evidence=("proposal:view-model-contract",),
        )

        projection = gap.to_dict()

        self.assertEqual(projection["category"], "not_implemented")
        self.assertEqual(projection["severity"], "info")
        self.assertEqual(projection["source_links"][0]["source_type"], "design")
        json.dumps(projection, sort_keys=True)

    def test_disabled_action_affordance_requires_reason_and_serializes(self) -> None:
        action = serve_triage.ActionAffordance(
            id="dispatch-agent",
            label="Dispatch agent",
            action="mutating",
            enabled=False,
            mutates_repository=True,
            disabled_reason="Agent dispatch is outside the safe-default MVP.",
        )

        projection = action.to_dict()

        self.assertFalse(projection["enabled"])
        self.assertTrue(projection["mutates_repository"])
        self.assertEqual(
            projection["disabled_reason"],
            "Agent dispatch is outside the safe-default MVP.",
        )
        with self.assertRaises(ValueError):
            serve_triage.ActionAffordance(
                id="missing-reason",
                label="Missing reason",
                action="preview",
                enabled=False,
            )
        with self.assertRaises(ValueError):
            serve_triage.ActionAffordance(
                id="unsafe-enabled",
                label="Unsafe enabled",
                action="mutating",
                enabled=True,
                mutates_repository=True,
            )

    def test_workspace_view_orders_lanes_and_cards_stably(self) -> None:
        ready = _card(
            "b-ready",
            display_name="Beta",
            readiness=serve_triage.ReadinessBadge(
                "ready",
                ready_leaf_count=1,
                evidence=("ready-leaf:WI-B",),
            ),
        )
        attention = _card(
            "a-attention",
            display_name="Alpha",
            validation=serve_triage.ValidationBadge(
                "error",
                error_count=1,
                evidence=("validate:error",),
            ),
        )
        workspace = serve_triage.build_workspace_view(
            workspace_mode="local",
            projects=(ready, attention),
            generated_at="2026-05-18T21:05:00Z",
        )

        self.assertEqual(
            [lane.id for lane in workspace.lanes],
            list(serve_triage.LANE_ORDER),
        )
        self.assertEqual(
            [card.project_id for card in workspace.projects], ["a-attention", "b-ready"]
        )
        lanes = {lane.id: lane for lane in workspace.lanes}
        self.assertEqual(lanes["needs_attention"].project_ids, ("a-attention",))
        self.assertEqual(lanes["ready_for_prompted_work"].project_ids, ("b-ready",))
        self.assertEqual(lanes["needs_attention"].evidence_refs, ("validate:error",))
        projection = workspace.to_dict()
        self.assertEqual(projection["projects"][0]["lane_id"], "needs_attention")
        json.dumps(projection, sort_keys=True)

    def test_planned_not_implemented_gap_does_not_force_validation_error(self) -> None:
        card = _card(
            "planned-gap",
            capability_gaps=(
                serve_triage.default_capability_gap_for_unimplemented(
                    "Project detail page",
                    "The detail contract exists before route rendering.",
                ),
            ),
        )

        assignment = serve_triage.classify_project_card(card)

        self.assertEqual(assignment.lane_id, "stable_complete")
        self.assertEqual(card.capability_gaps[0].category, "not_implemented")
        self.assertEqual(card.capability_gaps[0].severity, "info")


def _card(
    project_id: str,
    *,
    display_name: str | None = None,
    source_state: serve_triage.SourceState = "live",
    validation: serve_triage.ValidationBadge | None = None,
    readiness: serve_triage.ReadinessBadge | None = None,
    in_progress_work_item_count: int = 0,
    blocker_count: int = 0,
    capability_gaps: tuple[serve_triage.CapabilityGap, ...] = (),
) -> serve_triage.ProjectOperationalCard:
    return serve_triage.ProjectOperationalCard(
        project_id=project_id,
        display_name=display_name or project_id.title(),
        short_name=project_id,
        locator=f"/projects/{project_id}",
        source_state=source_state,
        validation=validation or serve_triage.ValidationBadge("valid"),
        readiness=readiness or serve_triage.ReadinessBadge("unknown"),
        in_progress_work_item_count=in_progress_work_item_count,
        blocker_count=blocker_count,
        capability_gaps=capability_gaps,
    )


if __name__ == "__main__":
    unittest.main()
