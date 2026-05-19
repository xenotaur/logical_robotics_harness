import os
import pathlib
import subprocess
import sys
import tempfile
import unittest


class ConversationCliTest(unittest.TestCase):
    def _repo_root(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parents[2]

    def _run_lrh(
        self, *args: str, cwd: pathlib.Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "lrh.cli.main", *args],
            check=False,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            cwd=cwd or self._repo_root(),
        )

    def _write_pdf(
        self,
        path: pathlib.Path,
        content_stream: bytes = b"BT (hello from ChatGPT PDF) Tj ET",
        *,
        pages_count: int = 1,
    ) -> None:
        pdf_bytes = b"\n".join(
            [
                b"%PDF-1.4",
                b"1 0 obj << /Type /Pages /Count "
                + str(pages_count).encode()
                + b" >> endobj",
                b"2 0 obj << /Type /Page /Parent 1 0 R >> endobj",
                b"3 0 obj << /Length " + str(len(content_stream)).encode() + b" >>",
                b"stream",
                content_stream,
                b"endstream",
                b"endobj",
                b"trailer << /Root 4 0 R >>",
                b"%%EOF",
            ]
        )
        path.write_bytes(pdf_bytes)

    def test_conversation_convert_pdf_help_describes_scope_and_privacy(self) -> None:
        completed = self._run_lrh("conversation", "convert-pdf", "--help")

        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        self.assertIn("convert-pdf", completed.stdout)
        self.assertIn("ChatGPT PDF conversation export", completed.stdout)
        self.assertIn("OCR and scanned PDFs are not supported", completed.stdout)
        self.assertIn("privacy=private", completed.stdout)
        self.assertIn("authority=non_authoritative_context", completed.stdout)
        self.assertIn("heuristic", completed.stdout)

    def test_conversation_help_lists_convert_pdf(self) -> None:
        completed = self._run_lrh("conversation", "--help")

        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        self.assertIn("convert-pdf", completed.stdout)

    def test_convert_pdf_writes_private_non_authoritative_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            input_path = temp_path / "conversation.pdf"
            output_path = temp_path / "conversation.md"
            self._write_pdf(input_path)

            completed = self._run_lrh(
                "conversation",
                "convert-pdf",
                str(input_path),
                "--out",
                str(output_path),
            )

            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            self.assertTrue(output_path.exists())
            written = output_path.read_text(encoding="utf-8")
            self.assertIn('privacy: "private"', written)
            self.assertIn('authority: "non_authoritative_context"', written)
            self.assertIn("hello from ChatGPT PDF", written)
            self.assertIn(
                f"Converted ChatGPT PDF transcript: {output_path}", completed.stdout
            )
            self.assertIn("Pages: 1", completed.stdout)
            self.assertIn("Privacy: private", completed.stdout)
            self.assertIn("Sensitivity: none_detected", completed.stdout)
            self.assertIn("Warnings: 1", completed.stdout)
            self.assertIn("warning: turn_boundaries_not_inferred", completed.stderr)

    def test_convert_pdf_refuses_overwrite_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            input_path = temp_path / "conversation.pdf"
            output_path = temp_path / "conversation.md"
            self._write_pdf(input_path)
            output_path.write_text("existing", encoding="utf-8")

            completed = self._run_lrh(
                "conversation",
                "convert-pdf",
                str(input_path),
                "--out",
                str(output_path),
            )

            self.assertEqual(completed.returncode, 1)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "existing")
            self.assertIn("Output already exists", completed.stderr)

    def test_convert_pdf_overwrites_with_force(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            input_path = temp_path / "conversation.pdf"
            output_path = temp_path / "conversation.md"
            self._write_pdf(input_path)
            output_path.write_text("existing", encoding="utf-8")

            completed = self._run_lrh(
                "conversation",
                "convert-pdf",
                str(input_path),
                "--out",
                str(output_path),
                "--force",
            )

            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            self.assertIn(
                "hello from ChatGPT PDF", output_path.read_text(encoding="utf-8")
            )

    def test_convert_pdf_sensitive_findings_warn_and_count(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            input_path = temp_path / "conversation.pdf"
            output_path = temp_path / "conversation.md"
            self._write_pdf(input_path, b"BT (email user@example.com) Tj ET")

            completed = self._run_lrh(
                "conversation",
                "convert-pdf",
                str(input_path),
                "--out",
                str(output_path),
            )

            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            self.assertIn(
                'sensitivity: "potential"', output_path.read_text(encoding="utf-8")
            )
            self.assertIn("Sensitivity: potential", completed.stdout)
            self.assertIn("Warnings: 2", completed.stdout)
            self.assertIn("potential sensitive content detected", completed.stderr)
            self.assertIn("warning: turn_boundaries_not_inferred", completed.stderr)

    def test_convert_pdf_no_frontmatter_summary_notes_metadata_omitted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            input_path = temp_path / "conversation.pdf"
            output_path = temp_path / "conversation.md"
            self._write_pdf(input_path)

            completed = self._run_lrh(
                "conversation",
                "convert-pdf",
                str(input_path),
                "--out",
                str(output_path),
                "--no-frontmatter",
            )

            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            self.assertEqual(
                output_path.read_text(encoding="utf-8"), "hello from ChatGPT PDF\n"
            )
            self.assertIn("Metadata: omitted (--no-frontmatter)", completed.stdout)
            self.assertNotIn("Privacy: private", completed.stdout)
            self.assertNotIn("Sensitivity:", completed.stdout)

    def test_convert_pdf_no_scan_sensitive_marks_unscanned(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            input_path = temp_path / "conversation.pdf"
            output_path = temp_path / "conversation.md"
            self._write_pdf(input_path, b"BT (email user@example.com) Tj ET")

            completed = self._run_lrh(
                "conversation",
                "convert-pdf",
                str(input_path),
                "--out",
                str(output_path),
                "--no-scan-sensitive",
            )

            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            written = output_path.read_text(encoding="utf-8")
            self.assertIn('sensitivity: "unscanned"', written)
            self.assertIn("Sensitivity: unscanned", completed.stdout)
            self.assertNotIn("potential sensitive content", completed.stderr)

    def test_convert_pdf_missing_input_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            completed = self._run_lrh(
                "conversation",
                "convert-pdf",
                str(temp_path / "missing.pdf"),
                "--out",
                str(temp_path / "conversation.md"),
            )

            self.assertEqual(completed.returncode, 1)
            self.assertIn("PDF input does not exist", completed.stderr)


if __name__ == "__main__":
    unittest.main()
