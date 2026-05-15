import pathlib
import tempfile
import unittest

from lrh.assist import run_report


class RunReportTest(unittest.TestCase):
    def test_success_report_is_deterministic_and_evidence_backed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            work_item = _write_work_item(root, _ready_work_item_text())
            report_input = run_report.RunReportInput(
                work_item_path=work_item,
                outcome="success",
                run_packet_path=root / "packets" / "WI-READY.md",
                validation_commands_run=("scripts/test",),
                validation_results=(
                    run_report.ValidationResult(
                        command="scripts/test",
                        status="pass",
                        evidence="logs/test.txt",
                    ),
                ),
                evidence_references=("logs/test.txt", "review-notes/manual.md"),
                artifact_references=("reports/WI-READY.md",),
                human_verification_tasks=("Review generated report before closeout.",),
                policy_gate_states=("manual_review: satisfied by reviewer",),
                human_gate_states=("human closeout: pending",),
                recommended_next_actions=("Human may close WI-READY after review.",),
                prompt_execution_record="project/executions/WI-READY/example.md",
            )

            first = run_report.render_run_report(report_input, project_root=root)
            second = run_report.render_run_report(report_input, project_root=root)

        self.assertEqual(first.diagnostics, ())
        self.assertEqual(first.markdown, second.markdown)
        self.assertIn("# Run Report: WI-READY", first.markdown)
        self.assertIn("- ID: `WI-READY`", first.markdown)
        self.assertIn("- Run packet: `packets/WI-READY.md`", first.markdown)
        self.assertIn("- Reported outcome: `success`", first.markdown)
        self.assertIn("- `scripts/test`", first.markdown)
        self.assertIn("- `scripts/test`: pass; evidence: logs/test.txt", first.markdown)
        self.assertIn("- logs/test.txt", first.markdown)
        self.assertIn("- reports/WI-READY.md", first.markdown)
        self.assertIn("- generated_report", first.markdown)
        self.assertIn("manual_review: satisfied by reviewer", first.markdown)
        self.assertIn("human closeout: pending", first.markdown)
        self.assertIn("replace prompt execution records", first.markdown)
        self.assertIn("project/executions/WI-READY/example.md", first.markdown)

    def test_supported_outcomes_render(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            work_item = _write_work_item(root, _ready_work_item_text())
            for outcome in run_report.outcome_choices():
                result = run_report.render_run_report(
                    run_report.RunReportInput(
                        work_item_path=work_item,
                        outcome=outcome,
                        validation_commands_run=("scripts/test",),
                        validation_results=(
                            run_report.ValidationResult("scripts/test", "not run"),
                        ),
                        evidence_references=("evidence/manual.md",),
                    ),
                    project_root=root,
                )
                self.assertIn(f"- Reported outcome: `{outcome}`", result.markdown)

    def test_missing_evidence_and_validation_results_are_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            work_item = _write_work_item(root, _ready_work_item_text())

            result = run_report.render_run_report(
                run_report.RunReportInput(
                    work_item_path=work_item,
                    outcome="success",
                ),
                project_root=root,
            )

        codes = {diagnostic.code for diagnostic in result.diagnostics}
        self.assertIn("EVIDENCE_REFERENCES_MISSING", codes)
        self.assertIn("SUCCESS_EVIDENCE_MISSING", codes)
        self.assertIn("VALIDATION_RESULTS_MISSING", codes)
        self.assertIn("## Unresolved Risks or Missing Evidence", result.markdown)
        self.assertIn("EVIDENCE_REFERENCES_MISSING", result.markdown)
        diagnostic_text = run_report.format_run_report_diagnostics(result.diagnostics)
        self.assertIn("unresolved review diagnostics", diagnostic_text)

    def test_non_ready_item_report_records_readiness_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            work_item = _write_work_item(
                root,
                """---
id: WI-NOT-READY
title: Not Ready
type: deliverable
status: proposed
---
""",
            )

            result = run_report.render_run_report(
                run_report.RunReportInput(
                    work_item_path=work_item,
                    outcome="blocked",
                ),
                project_root=root,
            )

        self.assertIn("EXECUTION_READINESS_NOT_READY", result.markdown)
        self.assertIn("human review required", result.markdown)

    def test_parse_validation_result_accepts_evidence(self) -> None:
        result = run_report.parse_validation_result(
            "scripts/test :: pass :: logs/test.txt"
        )

        self.assertEqual(result.command, "scripts/test")
        self.assertEqual(result.status, "pass")
        self.assertEqual(result.evidence, "logs/test.txt")


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
required_evidence:
  - passing_tests
artifacts_expected:
  - report
execution_ready: true
autonomy_level: manual
operation_risk: read_only
allowed_paths:
  - src/lrh/assist/
validation_commands:
  - scripts/test
required_evidence:
  - passing_tests
expected_artifacts:
  - generated_report
requires_human_approval: true
requires_human_merge: true
requires_human_closeout: true
policy_gates:
  - manual_review
agent_constraints:
  - do_not_call_agents
---

## Summary

Render a report for a bounded attempt.
"""
