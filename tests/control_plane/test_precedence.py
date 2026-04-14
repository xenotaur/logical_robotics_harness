import unittest

from lrh.control_plane import precedence


class TestPrecedenceResolver(unittest.TestCase):
    def test_resolves_simple_valid_state(self) -> None:
        state = precedence.ControlPlaneState(
            focus={
                "id": "FOCUS-1",
                "status": "active",
                "active_contributors": ["owner-1"],
            },
            work_items=(
                {
                    "id": "WI-2",
                    "related_focus": ["FOCUS-1"],
                    "owner": "owner-1",
                    "contributors": ["agent-1"],
                    "assigned_agents": ["agent-1"],
                },
                {
                    "id": "WI-1",
                    "related_focus": ["FOCUS-1"],
                    "owner": "owner-1",
                },
            ),
        )

        resolved = precedence.resolve_precedence(state)

        self.assertEqual(resolved.active_focus, state.focus)
        self.assertEqual(
            [item["id"] for item in resolved.in_scope_work_items],
            ["WI-1", "WI-2"],
        )
        self.assertEqual(resolved.active_contributors, ("agent-1", "owner-1"))
        self.assertEqual(resolved.consistency_issues, ())

    def test_conflicting_runtime_focus_signal(self) -> None:
        state = precedence.ControlPlaneState(
            focus={"id": "FOCUS-1", "status": "active"},
            work_items=(
                {"id": "WI-1", "related_focus": ["FOCUS-1"], "owner": "owner-1"},
            ),
        )

        resolved = precedence.resolve_precedence(
            state,
            runtime_invocation=precedence.RuntimeInvocation(focus_id="FOCUS-2"),
        )

        self.assertIsNone(resolved.active_focus)
        self.assertEqual(resolved.in_scope_work_items, state.work_items)
        self.assertIn(
            "runtime focus_id does not match loaded current focus id",
            resolved.consistency_issues,
        )

    def test_missing_optional_components(self) -> None:
        state = precedence.ControlPlaneState(
            focus={"id": "FOCUS-1", "status": "active"},
            work_items=(
                {"id": "WI-1", "related_focus": ["FOCUS-1"], "owner": "owner-1"},
                {"id": "WI-2", "related_focus": ["FOCUS-1"], "owner": "owner-2"},
            ),
            guardrails={"blocked_work_item_ids": ["WI-2"]},
        )

        invocation = precedence.RuntimeInvocation(
            work_item_ids=("WI-1", "WI-2"),
            contributor_ids=("owner-1", "owner-2"),
        )
        first = precedence.resolve_precedence(state, runtime_invocation=invocation)
        second = precedence.resolve_precedence(state, runtime_invocation=invocation)

        self.assertEqual([item["id"] for item in first.in_scope_work_items], ["WI-1"])
        self.assertEqual(first.active_contributors, ("owner-1",))
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
