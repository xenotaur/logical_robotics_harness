import datetime
import pathlib
import tempfile
import unittest
import zlib

from lrh.conversations import pdf_import

_SAMPLE_PDF_TEXT = """ChatGPT - LRH Project
Printed using ChatGPT to PDF, powered by PDFCrowd HTML to PDF API.
1/2
User: hello assistant@example.com
ChatGPT - LRH Project
2/2
Printed using ChatGPT to PDF, powered by PDFCrowd HTML to PDF API.
Assistant: world
"""


class PdfImportTest(unittest.TestCase):
    def test_convert_pdf_to_markdown_defaults_and_cleanup(self) -> None:
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
        self.assertEqual(1, transcript.frontmatter["page_count"])
        self.assertNotIn("1/2", transcript.body)
        self.assertNotIn("2/2", transcript.body)
        self.assertNotIn(pdf_import.PDFCROWD_FOOTER, transcript.body)
        self.assertNotIn("\nChatGPT - LRH Project\n\nAssistant:", transcript.body)
        markdown = transcript.to_markdown()
        self.assertIn('kind: "lrh_conversation_transcript"', markdown)
        self.assertIn('extracted_at: "2026-05-18T00:00:00+00:00"', markdown)
        self.assertIn("## Extracted Transcript", markdown)
        self.assertIn("assistant@example.com", markdown)
        markdown.encode("utf-8")

    def test_missing_file_raises_pdf_import_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_path = pathlib.Path(temp_dir) / "missing.pdf"

            with self.assertRaisesRegex(pdf_import.PdfImportError, "does not exist"):
                pdf_import.convert_chatgpt_pdf_to_markdown(missing_path)

    def test_empty_extraction_raises_pdf_import_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = pathlib.Path(temp_dir) / "empty.pdf"
            _write_simple_pdf(path, "")

            with self.assertRaisesRegex(
                pdf_import.PdfImportError, "Empty extracted PDF transcript"
            ):
                pdf_import.convert_chatgpt_pdf_to_markdown(path)

    def test_scanner_can_be_disabled(self) -> None:
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

    def test_extracts_escaped_parentheses_and_tj_array_strings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = pathlib.Path(temp_dir) / "escaped.pdf"
            content = (
                "BT\n"
                r"(Title with \(parentheses\) and line\nfeed) Tj"
                "\n"
                r"[(Array ) -120 (text\050ok\051)] TJ"
                "\nET\n"
            ).encode("latin-1")
            _write_pdf_with_content(path, content, page_count=2)

            transcript = pdf_import.convert_chatgpt_pdf_to_markdown(
                path,
                scan_sensitive=False,
                extracted_at=datetime.datetime(2026, 5, 18, tzinfo=datetime.UTC),
            )

        self.assertIn("Title with (parentheses) and line\nfeed", transcript.body)
        self.assertIn("Array text(ok)", transcript.body)
        self.assertEqual(2, transcript.frontmatter["page_count"])

    def test_extracts_text_from_flate_decode_stream(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = pathlib.Path(temp_dir) / "compressed.pdf"
            content = zlib.compress(b"BT\n(Title\nUser: hello) Tj\nET\n")
            _write_pdf_with_content(
                path,
                content,
                page_count=1,
                stream_dictionary_extra=b" /Filter /FlateDecode",
            )

            transcript = pdf_import.convert_chatgpt_pdf_to_markdown(
                path,
                scan_sensitive=False,
                extracted_at=datetime.datetime(2026, 5, 18, tzinfo=datetime.UTC),
            )

        self.assertIn("Title\nUser: hello", transcript.body)

    def test_encrypt_detection_uses_trailer_key_not_arbitrary_substring(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            false_positive_path = pathlib.Path(temp_dir) / "plain.pdf"
            _write_simple_pdf(false_positive_path, "Title\n/EncryptedData is just text")

            transcript = pdf_import.convert_chatgpt_pdf_to_markdown(
                false_positive_path,
                scan_sensitive=False,
                extracted_at=datetime.datetime(2026, 5, 18, tzinfo=datetime.UTC),
            )

            encrypted_path = pathlib.Path(temp_dir) / "encrypted.pdf"
            _write_simple_pdf(
                encrypted_path,
                "Title",
                trailer_extra=b" /Encrypt 6 0 R",
            )

            with self.assertRaisesRegex(pdf_import.PdfImportError, "Encrypted PDF"):
                pdf_import.convert_chatgpt_pdf_to_markdown(encrypted_path)

        self.assertIn("/EncryptedData is just text", transcript.body)

    def test_yaml_scalars_quote_ambiguous_strings(self) -> None:
        yaml_text = pdf_import._yaml_dump(
            {
                "leading_dash": "- maybe a list",
                "boolean_like": "true",
                "number_like": "1.0",
                "trailing_space": "value ",
                "quoted": "contains 'single' and \"double\" quotes",
            }
        )

        self.assertIn('leading_dash: "- maybe a list"', yaml_text)
        self.assertIn('boolean_like: "true"', yaml_text)
        self.assertIn('number_like: "1.0"', yaml_text)
        self.assertIn('trailing_space: "value "', yaml_text)
        self.assertIn(
            'quoted: "contains \'single\' and \\"double\\" quotes"', yaml_text
        )


def _write_simple_pdf(
    path: pathlib.Path,
    text: str,
    *,
    trailer_extra: bytes = b"",
) -> None:
    escaped = text.replace("\\", "\\\\").replace("(", r"\(").replace(")", r"\)")
    content = ("BT\n" "/F1 12 Tf\n" "36 760 Td\n" f"({escaped}) Tj\n" "ET\n").encode(
        "utf-8"
    )
    _write_pdf_with_content(path, content, page_count=1, trailer_extra=trailer_extra)


def _write_pdf_with_content(
    path: pathlib.Path,
    content: bytes,
    *,
    page_count: int,
    trailer_extra: bytes = b"",
    stream_dictionary_extra: bytes = b"",
) -> None:
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        f"2 0 obj << /Type /Pages /Count {page_count} /Kids [3 0 R] >> endobj\n".encode(
            "ascii"
        ),
        (
            b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> "
            b"endobj\n"
        ),
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        (
            b"5 0 obj << /Length "
            + str(len(content)).encode("ascii")
            + stream_dictionary_extra
            + b" >> stream\n"
            + content
            + b"endstream\nendobj\n"
        ),
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
        b"trailer\n<< /Size "
        + str(len(offsets)).encode("ascii")
        + b" /Root 1 0 R"
        + trailer_extra
        + b" >>\n"
        + f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    path.write_bytes(bytes(buffer))


if __name__ == "__main__":
    unittest.main()
