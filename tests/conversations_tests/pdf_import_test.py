import datetime
import pathlib
import tempfile
import unittest

from lrh.conversations import pdf_import

_SAMPLE_PDF_TEXT = """ChatGPT - LRH Project
Printed using ChatGPT to PDF, powered by PDFCrowd HTML to PDF API.
1/2
User: hello
assistant@example.com
ChatGPT - LRH Project

2/2
Printed using ChatGPT to PDF, powered by PDFCrowd HTML to PDF API.
Assistant: world
"""


class PdfImportTest(unittest.TestCase):
    def test_convert_pdf_to_markdown_defaults_and_cleanup(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = pathlib.Path(temp_dir) / "ChatGPT - LRH Project.pdf"
            _write_simple_pdf(path, _SAMPLE_PDF_TEXT)

            transcript = pdf_import.convert_chatgpt_pdf_to_markdown(
                path,
                extracted_at=datetime.datetime(2026, 5, 18, tzinfo=datetime.UTC),
            )

            self.assertEqual("private", transcript.frontmatter["privacy"])
            self.assertEqual(
                "non_authoritative_context", transcript.frontmatter["authority"]
            )
            self.assertEqual("chatgpt", transcript.frontmatter["source_tool"])
            self.assertEqual("chatgpt_pdf", transcript.frontmatter["source_adapter"])
            self.assertEqual("potential", transcript.frontmatter["sensitivity"])
            self.assertNotIn("1/2", transcript.body)
            self.assertNotIn("2/2", transcript.body)
            self.assertNotIn(pdf_import.PDFCROWD_FOOTER, transcript.body)
            self.assertNotIn("\nChatGPT - LRH Project\n\nAssistant:", transcript.body)

            markdown = transcript.to_markdown()
            self.assertIn("kind: lrh_conversation_transcript", markdown)
            self.assertIn('extracted_at: "2026-05-18T00:00:00+00:00"', markdown)
            self.assertIn("## Extracted Transcript", markdown)
            self.assertIn("assistant@example.com", markdown)
            markdown.encode("utf-8")

    def test_missing_file_raises_pdf_import_error(self):
        with self.assertRaisesRegex(pdf_import.PdfImportError, "does not exist"):
            pdf_import.convert_chatgpt_pdf_to_markdown(pathlib.Path("/tmp/missing.pdf"))

    def test_empty_extraction_raises_pdf_import_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = pathlib.Path(temp_dir) / "empty.pdf"
            _write_simple_pdf(path, "")
            with self.assertRaisesRegex(
                pdf_import.PdfImportError, "No extractable text"
            ):
                pdf_import.convert_chatgpt_pdf_to_markdown(path)

    def test_scanner_can_be_disabled(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = pathlib.Path(temp_dir) / "scan-off.pdf"
            _write_simple_pdf(path, "Title\nplain text only")
            transcript = pdf_import.convert_chatgpt_pdf_to_markdown(
                path,
                scan_sensitive=False,
                extracted_at=datetime.datetime(2026, 5, 18, tzinfo=datetime.UTC),
            )
            self.assertEqual("unscanned", transcript.frontmatter["sensitivity"])
            self.assertEqual(
                "not_run", transcript.frontmatter["sensitivity_scan"]["status"]
            )


def _write_simple_pdf(path: pathlib.Path, text: str) -> None:
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content = ("BT\n" "/F1 12 Tf\n" "36 760 Td\n" f"({escaped}) Tj\n" "ET\n").encode(
        "utf-8"
    )

    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Count 1 /Kids [3 0 R] >> endobj\n",
        (
            b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> "
            b"endobj\n"
        ),
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        b"5 0 obj << /Length "
        + str(len(content)).encode("ascii")
        + b" >> stream\n"
        + content
        + b"endstream\nendobj\n",
    ]

    buffer = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(buffer))
        buffer.extend(obj)
    xref_offset = len(buffer)
    buffer.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    buffer.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        buffer.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    buffer.extend(
        (
            f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    path.write_bytes(bytes(buffer))


if __name__ == "__main__":
    unittest.main()
