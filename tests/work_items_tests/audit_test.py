import json
import pathlib
import tempfile
import unittest

from lrh.work_items import audit as work_items_audit


class WorkItemAuditTest(unittest.TestCase):
    def test_json_audit_output_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self._write(
                root,
                "project/work_items/proposed/WI-ONE.md",
                (
                    "---\n"
                    "id: WI-ONE\n"
                    "status: proposed\n"
                    "blocked: false\n"
                    "blocked_reason: null\n"
                    "resolution: null\n"
                    "---\n"
                    "# WI-ONE\n"
                ),
            )

            payload = json.loads(
                work_items_audit.format_json(work_items_audit.audit_work_items(root))
            )

            self.assertEqual(payload["schema_version"], "1.0")
            self.assertEqual(payload["summary"]["items"], 1)
            self.assertEqual(payload["items"][0]["id"], "WI-ONE")
            self.assertIn("validation", payload)
            self.assertIn("warnings", payload)

    def test_markdown_audit_contains_expected_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self._write(
                root,
                "project/work_items/proposed/WI-ONE.md",
                "---\nid: WI-ONE\nstatus: proposed\n---\n# WI-ONE\n",
            )

            text = work_items_audit.format_markdown(
                work_items_audit.audit_work_items(root)
            )

            self.assertIn("# Work Item Lifecycle Audit", text)
            self.assertIn("## Summary", text)
            self.assertIn("## Deterministic validation diagnostics", text)
            self.assertIn("## Lifecycle findings", text)
            self.assertIn("## Semantic review guidance", text)

    def test_audit_handles_small_temporary_work_item_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self._write(
                root,
                "project/work_items/resolved/WI-DONE.md",
                (
                    "---\n"
                    "id: WI-DONE\n"
                    "status: resolved\n"
                    "resolution: null\n"
                    "---\n"
                    "# WI-DONE\n"
                ),
            )

            report = work_items_audit.audit_work_items(root)

            self.assertEqual(len(report.items), 1)
            findings = {finding.code for finding in report.items[0].findings}
            self.assertIn("terminal-missing-resolution", findings)

    def _write(self, root: pathlib.Path, rel: str, text: str) -> None:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
