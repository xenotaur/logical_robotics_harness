import hashlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lrh.conversations import codex_file_export

EXPORTED_AT = "2026-08-04T00:53:46+00:00"


class TestCodexFileExport(unittest.TestCase):
    def test_convert_codex_file_writes_manifest_frontmatter_and_body(self) -> None:
        transcript = "User: hello\nAssistant: hi\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "codex-session.txt"
            output_path = Path(temp_dir) / "export.md"
            source_path.write_text(transcript, encoding="utf-8")

            result = codex_file_export.convert_codex_file(
                source_path,
                output_path=output_path,
                source_id="codex-session-123",
                exported_at=EXPORTED_AT,
            )

            written = output_path.read_text(encoding="utf-8")
            self.assertEqual(result.markdown, written)
            self.assertTrue(written.startswith("---\n"))
            self.assertIn('kind: "lrh_codex_conversation_export"', written)
            self.assertIn('source_adapter: "codex_file_export"', written)
            self.assertIn('privacy: "private"', written)
            self.assertIn('authority: "non_authoritative_context"', written)
            self.assertIn('source_id: "codex-session-123"', written)
            self.assertIn("\nUser: hello\nAssistant: hi\n", written)

    def test_convert_codex_file_preserves_source_hash_and_statistics(self) -> None:
        transcript = "hello\nsnowman: \u2603"
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "codex.txt"
            output_path = Path(temp_dir) / "export.md"
            source_path.write_text(transcript, encoding="utf-8")

            result = codex_file_export.convert_codex_file(
                source_path,
                output_path=output_path,
                exported_at=EXPORTED_AT,
            )

            expected_hash = hashlib.sha256(transcript.encode("utf-8")).hexdigest()
            self.assertEqual(result.manifest.source_sha256, expected_hash)
            self.assertEqual(result.manifest.transcript_statistics.byte_count, 18)
            self.assertEqual(result.manifest.transcript_statistics.character_count, 16)
            self.assertEqual(result.manifest.transcript_statistics.line_count, 2)

    def test_convert_codex_file_propagates_sensitivity_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "codex.txt"
            output_path = Path(temp_dir) / "export.md"
            source_path.write_text("contact user@example.com", encoding="utf-8")

            result = codex_file_export.convert_codex_file(
                source_path,
                output_path=output_path,
                exported_at=EXPORTED_AT,
            )

            self.assertEqual(result.manifest.sensitivity, "potential")
            self.assertEqual(
                result.manifest.warnings,
                ("potential_sensitive_content_detected",),
            )
            self.assertIn('sensitivity: "potential"', result.markdown)
            self.assertIn('- "email"', result.markdown)

    def test_convert_codex_file_can_skip_sensitivity_scan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "codex.txt"
            output_path = Path(temp_dir) / "export.md"
            source_path.write_text("contact user@example.com", encoding="utf-8")

            result = codex_file_export.convert_codex_file(
                source_path,
                output_path=output_path,
                scan_sensitive=False,
                exported_at=EXPORTED_AT,
            )

            self.assertIsNone(result.sensitivity_result)
            self.assertEqual(result.manifest.sensitivity, "unscanned")
            self.assertEqual(
                result.manifest.sensitivity_scan, {"status": "not_scanned"}
            )

    def test_missing_input_raises_portable_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_path = Path(temp_dir) / "missing.txt"
            output_path = Path(temp_dir) / "export.md"

            with self.assertRaisesRegex(
                codex_file_export.CodexFileExportError, "does not exist"
            ):
                codex_file_export.convert_codex_file(
                    missing_path,
                    output_path=output_path,
                )

    def test_existing_output_requires_force(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "codex.txt"
            output_path = Path(temp_dir) / "export.md"
            source_path.write_text("hello", encoding="utf-8")
            output_path.write_text("existing", encoding="utf-8")

            with self.assertRaisesRegex(
                codex_file_export.CodexFileExportError, "already exists"
            ):
                codex_file_export.convert_codex_file(
                    source_path,
                    output_path=output_path,
                )

            codex_file_export.convert_codex_file(
                source_path,
                output_path=output_path,
                force=True,
                exported_at=EXPORTED_AT,
            )
            self.assertIn("hello", output_path.read_text(encoding="utf-8"))

    def test_rejects_same_source_and_output_even_with_force(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "codex.txt"
            source_path.write_text("hello", encoding="utf-8")

            with self.assertRaisesRegex(
                codex_file_export.CodexFileExportError, "different files"
            ):
                codex_file_export.convert_codex_file(
                    source_path,
                    output_path=source_path,
                    force=True,
                )

    def test_rejects_hard_linked_output_even_with_force(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "codex.txt"
            output_path = Path(temp_dir) / "hard-link.md"
            source_path.write_text("hello", encoding="utf-8")
            try:
                os.link(source_path, output_path)
            except OSError as err:
                self.skipTest(f"hard links unavailable: {err}")

            with self.assertRaisesRegex(
                codex_file_export.CodexFileExportError, "different files"
            ):
                codex_file_export.convert_codex_file(
                    source_path,
                    output_path=output_path,
                    force=True,
                )
            self.assertEqual(source_path.read_text(encoding="utf-8"), "hello")

    def test_stable_frontmatter_output(self) -> None:
        manifest = codex_file_export.build_file_export_manifest(
            transcript_text="hello\nworld",
            source_sha256="a" * 64,
            exported_at=EXPORTED_AT,
            source_id="codex-session-123",
            scan_result=None,
            scan_sensitive=False,
        )

        self.assertEqual(
            codex_file_export.render_codex_markdown("hello\nworld", manifest),
            """---
kind: "lrh_codex_conversation_export"
schema_version: 1
source_tool: "codex"
source_adapter: "codex_file_export"
privacy: "private"
authority: "non_authoritative_context"
sensitivity: "unscanned"
sensitivity_scan:
  status: "not_scanned"
source_id: "codex-session-123"
source_sha256: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
exported_at: "2026-08-04T00:53:46+00:00"
adapter_version: 1
warnings: []
transcript_statistics:
  byte_count: 11
  character_count: 11
  line_count: 2
---

hello
world
""",
        )

    @patch("sys.stderr", new_callable=io.StringIO)
    def test_run_convert_codex_file_cli_error_handling(
        self,
        mock_stderr: io.StringIO,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_path = Path(temp_dir) / "missing.txt"
            output_path = Path(temp_dir) / "export.md"

            result = codex_file_export.run_convert_codex_file_cli(
                [str(missing_path), "--out", str(output_path)],
                prog="lrh conversation convert-codex-file",
            )

            self.assertEqual(result, 1)
            self.assertIn("error: Codex source does not exist", mock_stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
