import tempfile
import unittest
from pathlib import Path

from lrh.conversations import pdf_import


def _minimal_pdf(content_stream: bytes, *, pages_count: int = 2) -> bytes:
    return b"\n".join(
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


class TestPdfImport(unittest.TestCase):
    def test_extracts_tj_string_with_escaped_parentheses(self) -> None:
        pdf_bytes = _minimal_pdf(b"BT (hello \\(review\\) world) Tj ET")

        extraction = pdf_import.extract_pdf_text(pdf_bytes)

        self.assertIn("hello (review) world", extraction.text)

    def test_extracts_tj_array_strings(self) -> None:
        pdf_bytes = _minimal_pdf(b"BT [(Hello) 120 ( from ) -20 (TJ)] TJ ET")

        extraction = pdf_import.extract_pdf_text(pdf_bytes)

        self.assertEqual(extraction.text, "Hello from TJ")

    def test_unescapes_pdf_string_escape_sequences_and_octal(self) -> None:
        pdf_bytes = _minimal_pdf(b"BT (line\\none\\040two\\t\\050x\\051) Tj ET")

        extraction = pdf_import.extract_pdf_text(pdf_bytes)

        self.assertEqual(extraction.text, "line\none two\t(x)")

    def test_encrypt_literal_outside_trailer_does_not_reject_pdf(self) -> None:
        pdf_bytes = _minimal_pdf(b"BT (/Encrypt and /EncryptedData are text) Tj ET")

        extraction = pdf_import.extract_pdf_text(pdf_bytes)

        self.assertIn("/Encrypt and /EncryptedData are text", extraction.text)

    def test_encrypt_key_in_trailer_rejects_pdf(self) -> None:
        pdf_bytes = b"\n".join(
            [
                b"%PDF-1.4",
                b"trailer << /Root 1 0 R /Encrypt 2 0 R >>",
                b"%%EOF",
            ]
        )

        with self.assertRaisesRegex(pdf_import.PdfImportError, "Encrypted"):
            pdf_import.extract_pdf_text(pdf_bytes)

    def test_page_count_uses_pages_count_not_page_token_count(self) -> None:
        pdf_bytes = _minimal_pdf(
            b"BT (/Type /Page text should not affect count) Tj ET",
            pages_count=12,
        )

        extraction = pdf_import.extract_pdf_text(pdf_bytes)

        self.assertEqual(extraction.page_count, 12)

    def test_yaml_scalar_quotes_ambiguous_strings(self) -> None:
        self.assertEqual(pdf_import._yaml_scalar("true"), '"true"')
        self.assertEqual(pdf_import._yaml_scalar("- leading"), '"- leading"')
        self.assertEqual(pdf_import._yaml_scalar(" spaced "), '" spaced "')
        self.assertEqual(pdf_import._yaml_scalar("1.0"), '"1.0"')

    def test_missing_input_uses_portable_temporary_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_path = Path(temp_dir) / "missing.pdf"
            with self.assertRaisesRegex(pdf_import.PdfImportError, "does not exist"):
                pdf_import.convert_pdf_file(missing_path)

    def test_convert_pdf_file_refuses_to_overwrite_without_force(self) -> None:
        pdf_bytes = _minimal_pdf(b"BT (hello) Tj ET")
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.pdf"
            output_path = Path(temp_dir) / "output.md"
            input_path.write_bytes(pdf_bytes)
            output_path.write_text("existing", encoding="utf-8")

            with self.assertRaisesRegex(pdf_import.PdfImportError, "already exists"):
                pdf_import.convert_pdf_file(input_path, output_path=output_path)

    def test_convert_pdf_file_writes_frontmatter_and_body(self) -> None:
        pdf_bytes = _minimal_pdf(b"BT (email user@example.com) Tj ET", pages_count=1)
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "true: file.pdf"
            output_path = Path(temp_dir) / "output.md"
            input_path.write_bytes(pdf_bytes)

            result = pdf_import.convert_pdf_file(
                input_path,
                output_path=output_path,
            )

            written = output_path.read_text(encoding="utf-8")
            self.assertEqual(result.markdown, written)
            self.assertIn('source_file: "true: file.pdf"', written)
            self.assertIn('sensitivity: "potential"', written)
            self.assertIn("email user@example.com", written)


if __name__ == "__main__":
    unittest.main()
