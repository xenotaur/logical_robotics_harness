import pathlib
import tempfile
import unittest

from lrh.assist import ready_work_item


class TestReadyWorkItemRequest(unittest.TestCase):
    def test_render_thin_work_item_includes_diagnostics_and_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            (root / ".git").mkdir()
            work_item = self._write_project_fixture(root)

            result = ready_work_item.render_ready_work_item_request(
                work_item,
                project_root=root,
            )

            self.assertFalse(result.readiness.is_ready)
            self.assertIn("missing Scope section", result.markdown)
            self.assertIn("missing Required Changes section", result.markdown)
            self.assertIn("missing Validation commands", result.markdown)
            self.assertIn("`project/roadmap/phase_03.md`", result.markdown)
            self.assertIn("`project/focus/current_focus.md`", result.markdown)
            self.assertIn("`project/design/example_design.md`", result.markdown)
            self.assertIn(
                "`project/workstreams/proposed/WS-EXAMPLE.md`", result.markdown
            )
            self.assertIn(
                "`project/work_items/proposed/WI-DEPENDENCY.md`", result.markdown
            )
            self.assertIn("Treat this as an open question", result.markdown)
            self.assertIn("- `## Open Questions`", result.markdown)

    def test_render_ready_work_item_does_not_mutate_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            (root / ".git").mkdir()
            work_item = self._write_project_fixture(root)
            original = work_item.read_text(encoding="utf-8")

            ready_work_item.render_ready_work_item_request(
                work_item,
                project_root=root,
            )

            self.assertEqual(work_item.read_text(encoding="utf-8"), original)

    def _write_project_fixture(self, root: pathlib.Path) -> pathlib.Path:
        roadmap = root / "project" / "roadmap" / "phase_03.md"
        focus = root / "project" / "focus" / "current_focus.md"
        design = root / "project" / "design" / "example_design.md"
        workstream = root / "project" / "workstreams" / "proposed" / "WS-EXAMPLE.md"
        dependency = root / "project" / "work_items" / "proposed" / "WI-DEPENDENCY.md"
        work_item = root / "project" / "work_items" / "proposed" / "WI-THIN.md"
        for path in (roadmap, focus, design, workstream, dependency, work_item):
            path.parent.mkdir(parents=True, exist_ok=True)
        roadmap.write_text(
            "---\n"
            "id: ROADMAP-PHASE-03\n"
            "title: Phase 3\n"
            "status: active\n"
            "---\n\n"
            "# Phase 3\n\n"
            "Execution planning.\n",
            encoding="utf-8",
        )
        focus.write_text(
            "---\n"
            "id: FOCUS-EXAMPLE\n"
            "title: Current Focus\n"
            "status: active\n"
            "---\n\n"
            "# Focus\n\n"
            "Current work.\n",
            encoding="utf-8",
        )
        design.write_text(
            "# Example Design\n\nDesign details.\n",
            encoding="utf-8",
        )
        workstream.write_text(
            "---\n"
            "id: WS-EXAMPLE\n"
            "title: Example Workstream\n"
            "status: proposed\n"
            "---\n\n"
            "# Workstream\n\n"
            "Workstream details.\n",
            encoding="utf-8",
        )
        dependency.write_text(
            "---\n"
            "id: WI-DEPENDENCY\n"
            "title: Dependency\n"
            "type: deliverable\n"
            "status: resolved\n"
            "blocked: false\n"
            "---\n\n"
            "## Summary\n\n"
            "Dependency details.\n",
            encoding="utf-8",
        )
        work_item.write_text(
            "---\n"
            "id: WI-THIN\n"
            "title: Thin item\n"
            "type: deliverable\n"
            "status: proposed\n"
            "blocked: false\n"
            "related_roadmap:\n"
            "  - ROADMAP-PHASE-03\n"
            "related_focus:\n"
            "  - FOCUS-EXAMPLE\n"
            "related_design:\n"
            "  - project/design/example_design.md\n"
            "related_workstreams:\n"
            "  - WS-EXAMPLE\n"
            "depends_on:\n"
            "  - WI-DEPENDENCY\n"
            "related_evidence:\n"
            "  - EV-MISSING\n"
            "acceptance:\n"
            "  - Reviewed proposal exists.\n"
            "---\n\n"
            "## Summary\n\n"
            "Needs more detail.\n",
            encoding="utf-8",
        )
        return work_item


if __name__ == "__main__":
    unittest.main()
