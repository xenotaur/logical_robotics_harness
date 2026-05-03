import json
import pathlib
import tempfile
import unittest

from lrh.work_items import validate as work_items_validate


class WorkItemsValidateTest(unittest.TestCase):
    def _write(self, root: pathlib.Path, rel: str, text: str) -> pathlib.Path:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_clean_bucketed_work_item_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self._write(
                root,
                "project/work_items/active/WI-OK-1.md",
                "---\nid: WI-OK-1\nstatus: active\n---\n\n# WI-OK-1\n",
            )
            result = work_items_validate.validate_work_items(root)
            self.assertEqual(result.errors, 0)

    def test_flat_warns_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self._write(
                root,
                "project/work_items/WI-FLAT-1.md",
                "---\nid: WI-FLAT-1\nstatus: proposed\n---\n",
            )
            result = work_items_validate.validate_work_items(root)
            self.assertEqual(result.errors, 0)
            self.assertGreaterEqual(result.warnings, 1)

    def test_duplicate_ids_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            content = "---\nid: WI-DUP-1\nstatus: active\n---\n"
            self._write(root, "project/work_items/active/WI-DUP-1.md", content)
            self._write(
                root,
                "project/work_items/proposed/WI-DUP-1.md",
                content.replace("active", "proposed"),
            )
            result = work_items_validate.validate_work_items(root)
            self.assertTrue(any(d.code == "duplicate-id" for d in result.diagnostics))

    def test_frontmatter_and_status_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self._write(
                root,
                "project/work_items/active/WI-BAD-1.md",
                "---\nid: WI-BAD-1\nstatus: wrong\n---\n",
            )
            self._write(
                root,
                "project/work_items/active/WI-NOSTATUS-1.md",
                "---\nid: WI-NOSTATUS-1\n---\n",
            )
            self._write(
                root,
                "project/work_items/active/WI-NOID-1.md",
                "---\nstatus: active\n---\n# WI-NOID-1\n",
            )
            result = work_items_validate.validate_work_items(root)
            codes = {d.code for d in result.diagnostics}
            self.assertIn("invalid-status", codes)
            self.assertIn("missing-frontmatter-status", codes)
            self.assertIn("missing-frontmatter-id", codes)

    def test_malformed_and_non_mapping_frontmatter_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self._write(
                root,
                "project/work_items/active/WI-MAL-1.md",
                "---\nid WI-MAL-1\n---\n",
            )
            self._write(
                root,
                "project/work_items/active/WI-LIST-1.md",
                "---\n- one\n- two\n---\n",
            )
            result = work_items_validate.validate_work_items(root)
            codes = {d.code for d in result.diagnostics}
            self.assertIn("malformed-frontmatter", codes)
            self.assertIn("frontmatter-not-mapping", codes)

    def test_json_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self._write(root, "project/work_items/notes.md", "hello")
            payload = json.loads(
                work_items_validate.format_json(
                    work_items_validate.validate_work_items(root)
                )
            )
            self.assertEqual(payload["schema_version"], "1.0")
            self.assertIn("errors", payload)
            self.assertIn("warnings", payload)
            self.assertIsInstance(payload["diagnostics"], list)

    def test_frontmatter_closing_delimiter_at_eof_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self._write(
                root,
                "project/work_items/active/WI-EOF-1.md",
                "---\nid: WI-EOF-1\nstatus: active\n---",
            )
            result = work_items_validate.validate_work_items(root)
            self.assertFalse(
                any(d.code == "malformed-frontmatter" for d in result.diagnostics)
            )

    def test_filename_and_unknown_bucket_are_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self._write(
                root,
                "project/work_items/custom/WI-NAMED-1.md",
                "---\nid: WI-OTHER-1\nstatus: active\n---\n",
            )
            result = work_items_validate.validate_work_items(root)
            severities = {d.code: d.severity for d in result.diagnostics}
            self.assertEqual(severities.get("unknown-bucket-directory"), "error")
            self.assertEqual(severities.get("filename-id-mismatch"), "error")

    def test_non_work_item_markdown_warning_is_emitted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self._write(root, "project/work_items/active/notes.md", "# Notes\n")
            result = work_items_validate.validate_work_items(root)
            codes = {d.code for d in result.diagnostics}
            self.assertIn("non-work-item-markdown", codes)
            self.assertIn("missing-reliable-id", codes)
