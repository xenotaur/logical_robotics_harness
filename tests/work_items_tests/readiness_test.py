import json
import pathlib
import tempfile
import unittest

from lrh.work_items import readiness as work_items_readiness


class WorkItemReadinessTest(unittest.TestCase):
    def test_json_schema_and_not_ready_recommendation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self._write(
                root,
                "project/work_items/proposed/WI-ONE.md",
                (
                    "---\n"
                    "id: WI-ONE\n"
                    "title: One\n"
                    "status: proposed\n"
                    "type: deliverable\n"
                    "blocked: false\n"
                    "---\n"
                    "# WI-ONE\n"
                ),
            )
            report = work_items_readiness.evaluate_readiness(project_root=root)
            payload = json.loads(work_items_readiness.format_json(report))
            self.assertEqual(payload["schema_version"], "1.0")
            self.assertEqual(payload["summary"]["not_ready"], 1)
            self.assertEqual(
                payload["items"][0]["recommended_next"],
                "lrh request ready-work-item WI-ONE",
            )

    def test_status_filter_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self._write(
                root,
                "project/work_items/proposed/WI-READY.md",
                (
                    "---\n"
                    "id: WI-READY\n"
                    "title: Ready\n"
                    "status: proposed\n"
                    "type: deliverable\n"
                    "blocked: false\n"
                    "---\n"
                    "# WI-READY\n\n"
                    "## Scope\n\n- scoped\n\n"
                    "## Required Changes\n\n- change\n\n"
                    "## Validation\n\n- scripts/test\n\n"
                    "## Acceptance Criteria\n\n- done\n"
                ),
            )
            self._write(
                root,
                "project/work_items/active/WI-ACTIVE.md",
                (
                    "---\n"
                    "id: WI-ACTIVE\n"
                    "title: Active\n"
                    "status: active\n"
                    "type: deliverable\n"
                    "blocked: false\n"
                    "---\n"
                    "# WI-ACTIVE\n"
                ),
            )
            report = work_items_readiness.evaluate_readiness(
                project_root=root,
                status="proposed",
            )
            self.assertEqual(len(report.items), 1)
            self.assertTrue(report.items[0].prompt_ready)
            text = work_items_readiness.format_markdown(report)
            self.assertIn("# Work Item Readiness", text)
            self.assertIn("## WI-READY", text)
            self.assertIn("prompt_ready: yes", text)

    def _write(self, root: pathlib.Path, rel: str, text: str) -> None:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
