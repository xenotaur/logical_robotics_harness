import tempfile
import unittest
from pathlib import Path

from lrh.control.loader import find_project_dir, load_project
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


class TestControlLoader(unittest.TestCase):
    def test_load_project_from_repo_root(self) -> None:
        state = load_project(Path("."))

        self.assertEqual(state.current_focus.id, "FOCUS-CONTROL-PLANE-SEMANTICS")
        self.assertIn("WI-0001", state.work_items_by_id)
        self.assertIn("anthony", state.contributors_by_id)

        related = state.work_items_for_focus(state.current_focus.id)
        self.assertTrue(any(item.id == "WI-0001" for item in related))

    def test_find_project_dir_supports_project_root_or_repo_root(self) -> None:
        self.assertEqual(find_project_dir(Path(".")), Path("project").resolve())
        self.assertEqual(find_project_dir(Path("project")), Path("project").resolve())

    def test_parse_markdown_file_reads_from_disk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "sample.md"
            path.write_text("---\nid: TEST\n---\nbody\n", encoding="utf-8")

            parsed = parse_markdown_file(path)

            self.assertEqual(parsed.frontmatter["id"], "TEST")
            self.assertEqual(parsed.body, "body\n")


if __name__ == "__main__":
    unittest.main()
