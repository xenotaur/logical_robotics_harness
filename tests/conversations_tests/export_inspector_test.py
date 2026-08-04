import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lrh.conversations import codex_file_export, export_inspector

EXPORTED_AT = "2026-08-04T19:44:28+00:00"


class TestConversationExportInspector(unittest.TestCase):
    def test_valid_export_reports_manifest_metadata_without_transcript_text(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path, export_path = _write_export(temp_dir, "User: secret\n")

            inspection = export_inspector.inspect_export(
                export_path,
                source_path=source_path,
            )

            self.assertTrue(inspection.valid, inspection.errors)
            self.assertTrue(inspection.manifest_valid)
            self.assertEqual(inspection.statistic_comparison.status, "match")
            self.assertEqual(inspection.source_hash.status, "match")
            mapping = inspection.to_mapping()
            self.assertEqual(mapping["privacy"], "private")
            self.assertEqual(mapping["authority"], "non_authoritative_context")
            self.assertEqual(mapping["sensitivity"], "none_detected")
            rendered_text = export_inspector.format_text(inspection)
            rendered_json = export_inspector.format_json(inspection)
            self.assertNotIn("User: secret", rendered_text)
            self.assertNotIn("User: secret", rendered_json)

    def test_accepts_export_renderer_added_trailing_newline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _source_path, export_path = _write_export(temp_dir, "hello")

            inspection = export_inspector.inspect_export(export_path)

            self.assertTrue(inspection.valid, inspection.errors)
            self.assertEqual(inspection.statistic_comparison.status, "match")
            self.assertEqual(
                inspection.statistic_comparison.artifact.character_count,
                5,
            )

    def test_body_statistic_drift_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _source_path, export_path = _write_export(temp_dir, "hello")
            export_path.write_text(
                export_path.read_text(encoding="utf-8") + "tampered\n",
                encoding="utf-8",
            )

            inspection = export_inspector.inspect_export(export_path)

            self.assertFalse(inspection.valid)
            self.assertEqual(inspection.statistic_comparison.status, "mismatch")
            self.assertIn("byte_count", inspection.statistic_comparison.mismatches)
            self.assertIn("transcript_statistics", inspection.errors[0])

    def test_extra_trailing_newline_drift_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _source_path, export_path = _write_export(temp_dir, "hello\n")
            export_path.write_text(
                export_path.read_text(encoding="utf-8") + "\n",
                encoding="utf-8",
            )

            inspection = export_inspector.inspect_export(export_path)

            self.assertFalse(inspection.valid)
            self.assertEqual(inspection.statistic_comparison.status, "mismatch")
            self.assertIn("line_count", inspection.statistic_comparison.mismatches)

    def test_hash_mismatch_is_invalid_when_source_supplied(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path, export_path = _write_export(temp_dir, "hello")
            source_path.write_text("changed", encoding="utf-8")

            inspection = export_inspector.inspect_export(
                export_path,
                source_path=source_path,
            )

            self.assertFalse(inspection.valid)
            self.assertEqual(inspection.source_hash.status, "mismatch")

    def test_missing_source_is_distinct_from_not_supplied(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _source_path, export_path = _write_export(temp_dir, "hello")

            without_source = export_inspector.inspect_export(export_path)
            with_missing_source = export_inspector.inspect_export(
                export_path,
                source_path=Path(temp_dir) / "missing.txt",
            )

            self.assertTrue(without_source.valid)
            self.assertEqual(without_source.source_hash.status, "not_supplied")
            self.assertFalse(with_missing_source.valid)
            self.assertEqual(with_missing_source.source_hash.status, "source_missing")

    def test_non_file_source_is_invalid_when_source_supplied(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _source_path, export_path = _write_export(temp_dir, "hello")

            inspection = export_inspector.inspect_export(
                export_path,
                source_path=Path(temp_dir),
            )

            self.assertFalse(inspection.valid)
            self.assertEqual(inspection.source_hash.status, "source_not_file")

    def test_malformed_manifest_reports_invalid_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = Path(temp_dir) / "broken.md"
            export_path.write_text("---\nkind: [\n---\n\nhello\n", encoding="utf-8")

            inspection = export_inspector.inspect_export(export_path)

            self.assertFalse(inspection.valid)
            self.assertFalse(inspection.manifest_valid)
            self.assertIn("manifest:", inspection.errors[0])

    def test_invalid_manifest_field_reports_invalid_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _source_path, export_path = _write_export(temp_dir, "hello")
            export_path.write_text(
                export_path.read_text(encoding="utf-8").replace(
                    'source_tool: "codex"',
                    'source_tool: "chatgpt"',
                ),
                encoding="utf-8",
            )

            inspection = export_inspector.inspect_export(export_path)

            self.assertFalse(inspection.valid)
            self.assertFalse(inspection.manifest_valid)
            self.assertIn("source_tool", inspection.errors[0])

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_run_inspect_export_cli_json_is_stable(
        self,
        mock_stdout: io.StringIO,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path, export_path = _write_export(temp_dir, "hello")

            result = export_inspector.run_inspect_export_cli(
                [
                    str(export_path),
                    "--source",
                    str(source_path),
                    "--format",
                    "json",
                ],
                prog="lrh conversation inspect-export",
            )

            self.assertEqual(result, 0)
            loaded = json.loads(mock_stdout.getvalue())
            self.assertEqual(loaded["source_hash"]["status"], "match")
            self.assertEqual(loaded["transcript_statistics"]["status"], "match")
            self.assertNotIn("hello", mock_stdout.getvalue())

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_run_inspect_export_cli_text_is_stable(
        self,
        mock_stdout: io.StringIO,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path, export_path = _write_export(temp_dir, "hello")

            result = export_inspector.run_inspect_export_cli(
                [str(export_path), "--source", str(source_path)],
                prog="lrh conversation inspect-export",
            )

            self.assertEqual(result, 0)
            output = mock_stdout.getvalue()
            self.assertIn("Valid: yes\n", output)
            self.assertIn("Privacy: private\n", output)
            self.assertIn("Transcript statistics: match\n", output)
            self.assertIn("Source hash: match\n", output)
            self.assertNotIn("hello", output)

    @patch("sys.stderr", new_callable=io.StringIO)
    def test_run_inspect_export_cli_missing_file_is_tool_error(
        self,
        mock_stderr: io.StringIO,
    ) -> None:
        result = export_inspector.run_inspect_export_cli(
            ["/no/such/export.md"],
            prog="lrh conversation inspect-export",
        )

        self.assertEqual(result, 2)
        self.assertIn("error: export does not exist", mock_stderr.getvalue())


def _write_export(temp_dir: str, transcript: str) -> tuple[Path, Path]:
    root = Path(temp_dir)
    source_path = root / "codex.txt"
    export_path = root / "export.md"
    source_path.write_text(transcript, encoding="utf-8")
    codex_file_export.convert_codex_file(
        source_path,
        output_path=export_path,
        exported_at=EXPORTED_AT,
    )
    return source_path, export_path


if __name__ == "__main__":
    unittest.main()
