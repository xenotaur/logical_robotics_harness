import pathlib
import tempfile
import unittest

from lrh.assist import run_packet


class RunPacketTest(unittest.TestCase):
    def test_execution_ready_work_item_renders_deterministic_packet(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            work_item = _write_work_item(root, _ready_work_item_text())

            first = run_packet.render_run_packet_from_work_item(
                work_item,
                project_root=root,
            )
            second = run_packet.render_run_packet_from_work_item(
                work_item,
                project_root=root,
            )

        self.assertEqual(first.diagnostics, ())
        self.assertEqual(first.markdown, second.markdown)
        self.assertIn("# Dry-Run Run Packet: WI-READY", first.markdown)
        self.assertIn("- ID: `WI-READY`", first.markdown)
        self.assertIn("- Workstreams: `WS-EXECUTION`", first.markdown)
        self.assertIn("- Focus: `FOCUS-EXECUTION`", first.markdown)
        self.assertIn("- Roadmap: `ROADMAP-PHASE-03`", first.markdown)
        self.assertIn("- Design: `project/design/execution.md`", first.markdown)
        self.assertIn("## Task Summary", first.markdown)
        self.assertIn("Render a packet for a bounded work item.", first.markdown)
        self.assertIn("## Required Changes", first.markdown)
        self.assertIn("- Add packet rendering.", first.markdown)
        self.assertIn("## Allowed Paths\n\n- src/lrh/assist/", first.markdown)
        self.assertIn("## Forbidden Paths\n\n- .github/workflows/", first.markdown)
        self.assertIn("- `scripts/test`", first.markdown)
        self.assertIn("- Human approval required before execution: yes", first.markdown)
        self.assertIn("- Autonomy level: `manual`", first.markdown)
        self.assertIn("- None. The selected work item passed", first.markdown)
        self.assertIn("dry-run/manual artifact", first.markdown)

    def test_missing_readiness_fields_render_diagnostic_packet(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            work_item = _write_work_item(
                root,
                """---
id: WI-NOT-READY
title: Not Ready
type: deliverable
status: proposed
execution_ready: true
---

## Summary

Missing readiness.
""",
            )

            result = run_packet.render_run_packet_from_work_item(
                work_item,
                project_root=root,
            )

        self.assertNotEqual(result.diagnostics, ())
        self.assertIn(
            "# Dry-Run Run Packet Review Required: WI-NOT-READY",
            result.markdown,
        )
        self.assertIn("EXECUTION_READINESS_REQUIRED_FIELD_MISSING", result.markdown)
        diagnostic_text = run_packet.format_readiness_diagnostics(result.diagnostics)
        self.assertIn("not execution-ready", diagnostic_text)
        self.assertIn(
            "missing execution-readiness field 'allowed_paths'", diagnostic_text
        )

    def test_non_execution_ready_work_item_has_review_required_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            work_item = _write_work_item(
                root,
                """---
id: WI-PLANNING
title: Planning Item
type: investigation
status: proposed
---

## Summary

Not opted in.
""",
            )

            result = run_packet.render_run_packet_from_work_item(work_item)

        self.assertEqual(len(result.diagnostics), 1)
        self.assertEqual(
            result.diagnostics[0].code,
            "EXECUTION_READINESS_NOT_READY",
        )
        self.assertIn("execution_ready must be true", result.markdown)


def _write_work_item(root: pathlib.Path, text: str) -> pathlib.Path:
    path = root / "project" / "work_items" / "proposed" / "WI-READY.md"
    path.parent.mkdir(parents=True)
    path.write_text(text, encoding="utf-8")
    return path


def _ready_work_item_text() -> str:
    return """---
id: WI-READY
title: Ready Work Item
type: deliverable
status: proposed
related_focus:
  - FOCUS-EXECUTION
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-EXECUTION
related_design:
  - project/design/execution.md
depends_on:
  - WI-READINESS
forbidden_actions:
  - force_push
required_evidence:
  - passing_tests
artifacts_expected:
  - run_packet
execution_ready: true
autonomy_level: manual
operation_risk: read_only
allowed_paths:
  - src/lrh/assist/
forbidden_paths:
  - .github/workflows/
validation_commands:
  - scripts/test
expected_artifacts:
  - generated_packet
requires_human_approval: true
requires_human_merge: true
requires_human_closeout: true
policy_gates:
  - manual_review
agent_constraints:
  - do_not_call_agents
---

## Summary

Render a packet for a bounded work item.

## Required Changes

- Add packet rendering.
- Add tests.

## Scope

- Safe-default request artifact only.
"""


if __name__ == "__main__":
    unittest.main()
