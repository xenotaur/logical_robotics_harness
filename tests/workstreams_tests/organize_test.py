"""Tests for workstream lifecycle bucket organization."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lrh.workstreams import organize as workstreams_organize


class WorkstreamOrganizeTest(unittest.TestCase):
    def test_dry_run_proposes_move_without_mutating_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = _write_workstream(root, "active", "WS-ALPHA", "resolved")
            original = source.read_text(encoding="utf-8")

            plan = workstreams_organize.plan_organization(root)
            report = workstreams_organize.build_text_report(plan)

            self.assertEqual(len(plan.planned_moves()), 1)
            self.assertIn("Would move:", report)
            self.assertIn("project/workstreams/active/WS-ALPHA.md", report)
            self.assertIn("project/workstreams/resolved/WS-ALPHA.md", report)
            self.assertTrue(source.exists())
            self.assertFalse(
                (root / "project/workstreams/resolved/WS-ALPHA.md").exists()
            )
            self.assertEqual(source.read_text(encoding="utf-8"), original)

    def test_apply_moves_mismatched_workstream_and_preserves_contents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = _write_workstream(root, "proposed", "WS-BETA", "active")
            original = source.read_bytes()

            plan = workstreams_organize.plan_organization(root)
            workstreams_organize.apply_plan(plan)

            target = root / "project/workstreams/active/WS-BETA.md"
            self.assertFalse(source.exists())
            self.assertTrue(target.exists())
            self.assertEqual(target.read_bytes(), original)

    def test_apply_leaves_already_correct_workstream_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = _write_workstream(root, "active", "WS-GAMMA", "active")
            original = path.read_text(encoding="utf-8")

            plan = workstreams_organize.plan_organization(root)
            report = workstreams_organize.build_text_report(plan)
            workstreams_organize.apply_plan(plan)

            self.assertEqual(plan.planned_moves(), [])
            self.assertEqual(report, "Workstreams already organized.")
            self.assertTrue(path.exists())
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_readme_and_placeholder_files_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            proposed = root / "project/workstreams/proposed"
            proposed.mkdir(parents=True)
            (root / "project/workstreams/README.md").write_text("# Index\n")
            (proposed / "README.md").write_text("# Proposed\n")
            (proposed / ".placeholder.md").write_text("placeholder\n")
            (proposed / "WS-DELTA.md").write_text("not valid workstream\n")

            plan = workstreams_organize.plan_organization(root)
            report = workstreams_organize.build_text_report(plan)

            self.assertEqual(len(plan.inspected), 1)
            self.assertIn("Skipped:", report)
            self.assertIn("WS-DELTA.md", report)
            self.assertNotIn("README.md", report)
            self.assertNotIn(".placeholder.md", report)

    def test_invalid_status_is_skipped_and_not_moved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = _write_workstream(root, "active", "WS-EPSILON", "done")

            plan = workstreams_organize.plan_organization(root)
            report = workstreams_organize.build_text_report(plan)
            workstreams_organize.apply_plan(plan)

            self.assertEqual(plan.planned_moves(), [])
            self.assertIn("Skipped:", report)
            self.assertIn("unsupported status 'done'", report)
            self.assertTrue(source.exists())

    def test_destination_conflict_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = _write_workstream(root, "proposed", "WS-ZETA", "active")
            target = _write_workstream(root, "active", "WS-ZETA", "active")

            plan = workstreams_organize.plan_organization(root)
            report = workstreams_organize.build_text_report(plan)

            self.assertIn("Blocked:", report)
            self.assertIn("target collision: target file already exists", report)
            with self.assertRaisesRegex(ValueError, "refusing to move"):
                workstreams_organize.apply_plan(plan)
            self.assertTrue(source.exists())
            self.assertTrue(target.exists())

    def test_multiple_bucket_moves_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_workstream(root, "active", "WS-BETA", "resolved")
            _write_workstream(root, "resolved", "WS-ALPHA", "proposed")

            plan = workstreams_organize.plan_organization(root)
            report = workstreams_organize.build_text_report(plan)

            self.assertEqual(
                [item.workstream_id for item in plan.planned_moves()],
                ["WS-BETA", "WS-ALPHA"],
            )
            self.assertLess(report.index("WS-BETA.md"), report.index("WS-ALPHA.md"))


def _write_workstream(root: Path, bucket: str, workstream_id: str, status: str) -> Path:
    path = root / "project" / "workstreams" / bucket / f"{workstream_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                f"id: {workstream_id}",
                "kind: planning_node",
                f"title: {workstream_id} title",
                f"status: {status}",
                "stage: planned",
                "---",
                "",
                f"# {workstream_id}",
                "",
                "Body text remains unchanged.",
            ]
        ),
        encoding="utf-8",
    )
    return path


if __name__ == "__main__":
    unittest.main()
