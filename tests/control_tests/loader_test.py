import tempfile
import unittest
from pathlib import Path

from lrh.control.loader import (
    find_project_dir,
    load_project,
    load_workstreams_from_project_dir_permissive,
)


class TestControlLoader(unittest.TestCase):
    def test_load_project_from_repo_root(self) -> None:
        state = load_project(Path("."))

        self.assertEqual(state.current_focus.id, "FOCUS-EXECUTION-FRAMEWORK-PLANNING")
        self.assertIn("WI-0001", state.work_items_by_id)
        self.assertIn("anthony", state.contributors_by_id)

        related = state.work_items_for_focus(state.current_focus.id)
        self.assertTrue(
            any(item.id == "WI-EXECUTION-READINESS-SCHEMA" for item in related)
        )

    def test_find_project_dir_supports_project_root_or_repo_root(self) -> None:
        self.assertEqual(find_project_dir(Path(".")), Path("project").resolve())
        self.assertEqual(find_project_dir(Path("project")), Path("project").resolve())

    def test_load_project_allows_blank_optional_contributor_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "project" / "focus").mkdir(parents=True)
            (root / "project" / "work_items" / "active").mkdir(parents=True)
            (root / "project" / "contributors").mkdir(parents=True)

            (root / "project" / "focus" / "current_focus.md").write_text(
                "---\nid: FOCUS-1\ntitle: Focus\nstatus: active\n---\n",
                encoding="utf-8",
            )
            (root / "project" / "work_items" / "active" / "WI-1.md").write_text(
                "---\nid: WI-1\ntitle: Task\ntype: deliverable\nstatus: active\n---\n",
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
            (root / "project" / "work_items" / "active").mkdir(parents=True)
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
                (root / "project" / "work_items" / "active" / name).write_text(
                    """---
id: WI-1
title: Task
type: deliverable
status: active
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
            (root / "project" / "work_items" / "active").mkdir(parents=True)
            (root / "project" / "contributors" / "agents").mkdir(parents=True)

            (root / "project" / "focus" / "current_focus.md").write_text(
                "---\nid: FOCUS-1\ntitle: Focus\nstatus: active\n---\n",
                encoding="utf-8",
            )
            (root / "project" / "work_items" / "active" / "WI-1.md").write_text(
                "---\nid: WI-1\ntitle: Task\ntype: deliverable\nstatus: active\n---\n",
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

    def test_load_workstreams_from_project_dir_permissive_catches_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            project_dir = root / "project"
            workstreams_dir = project_dir / "workstreams" / "active"
            workstreams_dir.mkdir(parents=True)

            (workstreams_dir / "WS-VALID.md").write_text(
                "---\n"
                "id: WS-VALID\n"
                "kind: feature\n"
                "title: Valid\n"
                "status: active\n"
                "stage: planning\n"
                "---\n",
                encoding="utf-8",
            )
            (workstreams_dir / "WS-INVALID.md").write_text(
                "Not a valid markdown with frontmatter",
                encoding="utf-8",
            )

            workstreams, warnings = load_workstreams_from_project_dir_permissive(
                project_dir
            )

            self.assertEqual(len(workstreams), 1)
            self.assertEqual(workstreams[0].id, "WS-VALID")

            self.assertEqual(len(warnings), 1)
            self.assertIn(
                "Skipped active/WS-INVALID.md: markdown file must begin with "
                "YAML frontmatter",
                warnings[0],
            )


if __name__ == "__main__":
    unittest.main()
