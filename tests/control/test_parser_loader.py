import tempfile
import unittest
from pathlib import Path

from lrh.control.loader import find_project_dir, load_project
from lrh.control.parser import parse_markdown_file, parse_markdown_text


class TestControlParser(unittest.TestCase):
    def test_parse_markdown_text_frontmatter_and_body(self) -> None:
        parsed = parse_markdown_text("""---
id: SAMPLE
contributors: []
items:
  - one
  - two
status: active
---

# Body

Hello.
""")

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

    def test_load_project_allows_blank_optional_contributor_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "project" / "focus").mkdir(parents=True)
            (root / "project" / "work_items").mkdir(parents=True)
            (root / "project" / "contributors").mkdir(parents=True)

            (root / "project" / "focus" / "current_focus.md").write_text(
                "---\nid: FOCUS-1\ntitle: Focus\nstatus: active\n---\n",
                encoding="utf-8",
            )
            (root / "project" / "work_items" / "WI-1.md").write_text(
                "---\nid: WI-1\ntitle: Task\ntype: deliverable\nstatus: ready\n---\n",
                encoding="utf-8",
            )
            (root / "project" / "contributors" / "person.md").write_text(
                """---
id: person-1
type: human
roles:
  - editor
display_name: Person
status: active
github:
description:
---""",
                encoding="utf-8",
            )

            state = load_project(root)

            contributor = state.contributors_by_id["person-1"]
            self.assertIsNone(contributor.github)
            self.assertIsNone(contributor.description)

    def test_load_project_rejects_duplicate_work_item_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "project" / "focus").mkdir(parents=True)
            (root / "project" / "work_items").mkdir(parents=True)
            (root / "project" / "contributors").mkdir(parents=True)

            (root / "project" / "focus" / "current_focus.md").write_text(
                "---\nid: FOCUS-1\ntitle: Focus\nstatus: active\n---\n",
                encoding="utf-8",
            )
            (root / "project" / "contributors" / "person.md").write_text(
                """---
id: person-1
type: human
roles: [editor]
display_name: Person
status: active
---
""",
                encoding="utf-8",
            )
            for name in ("WI-A.md", "WI-B.md"):
                (root / "project" / "work_items" / name).write_text(
                    """---
id: WI-1
title: Task
type: deliverable
status: ready
---
""",
                    encoding="utf-8",
                )

            with self.assertRaisesRegex(ValueError, "duplicate work item id: WI-1"):
                load_project(root)

    def test_load_project_rejects_duplicate_contributor_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "project" / "focus").mkdir(parents=True)
            (root / "project" / "work_items").mkdir(parents=True)
            (root / "project" / "contributors" / "agents").mkdir(parents=True)

            (root / "project" / "focus" / "current_focus.md").write_text(
                "---\nid: FOCUS-1\ntitle: Focus\nstatus: active\n---\n",
                encoding="utf-8",
            )
            (root / "project" / "work_items" / "WI-1.md").write_text(
                "---\nid: WI-1\ntitle: Task\ntype: deliverable\nstatus: ready\n---\n",
                encoding="utf-8",
            )
            for path in (
                root / "project" / "contributors" / "one.md",
                root / "project" / "contributors" / "agents" / "two.md",
            ):
                path.write_text(
                    """---
id: dup-1
type: human
roles: [editor]
display_name: Person
status: active
---
""",
                    encoding="utf-8",
                )

            with self.assertRaisesRegex(ValueError, "duplicate contributor id: dup-1"):
                load_project(root)

    def test_parse_markdown_file_reads_from_disk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "sample.md"
            path.write_text("---\nid: TEST\n---\nbody\n", encoding="utf-8")

            parsed = parse_markdown_file(path)

            self.assertEqual(parsed.frontmatter["id"], "TEST")
            self.assertEqual(parsed.body, "body\n")


if __name__ == "__main__":
    unittest.main()
