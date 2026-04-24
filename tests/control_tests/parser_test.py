import tempfile
import unittest
from pathlib import Path

from lrh.control.parser import parse_markdown_file, parse_markdown_text


class TestControlParser(unittest.TestCase):
    def test_parse_markdown_text_frontmatter_and_body(self) -> None:
        parsed = parse_markdown_text(
            """---
id: SAMPLE
contributors: []
items:
  - one
  - two
status: active
---

# Body

Hello.
"""
        )

        self.assertEqual(parsed.frontmatter["id"], "SAMPLE")
        self.assertEqual(parsed.frontmatter["contributors"], [])
        self.assertEqual(parsed.frontmatter["items"], ["one", "two"])
        self.assertEqual(parsed.body, "\n# Body\n\nHello.\n")

    def test_parse_markdown_text_accepts_closing_delimiter_at_eof(self) -> None:
        parsed = parse_markdown_text("---\nid: EOF\n---")

        self.assertEqual(parsed.frontmatter["id"], "EOF")
        self.assertEqual(parsed.body, "")

    def test_parse_empty_scalar_as_null(self) -> None:
        parsed = parse_markdown_text("---\ngithub:\ndescription:\n---\n")

        self.assertIsNone(parsed.frontmatter["github"])
        self.assertIsNone(parsed.frontmatter["description"])

    def test_parse_markdown_file_reads_from_disk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "sample.md"
            path.write_text("---\nid: TEST\n---\nbody\n", encoding="utf-8")

            parsed = parse_markdown_file(path)

            self.assertEqual(parsed.frontmatter["id"], "TEST")
            self.assertEqual(parsed.body, "body\n")


if __name__ == "__main__":
    unittest.main()
