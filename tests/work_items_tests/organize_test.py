import pathlib
import tempfile
import unittest

from lrh.work_items import organize as work_items_organize


class OrganizeTest(unittest.TestCase):
    def test_plan_h1_and_move(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            path = root / "project/work_items/WI-ALPHA-1.md"
            path.parent.mkdir(parents=True)
            path.write_text("# WI-ALPHA-1\n\nIn progress work.", encoding="utf-8")
            plan = work_items_organize.plan_organization(root)
            item = plan.inspected[0]
            self.assertTrue(item.add_frontmatter)
            self.assertEqual(item.inferred_status, "active")
            self.assertIn("/active/", str(item.target))

    def test_skip_unreliable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            path = root / "project/work_items/notes.md"
            path.parent.mkdir(parents=True)
            path.write_text("# Notes\n\nNo work item id.", encoding="utf-8")
            plan = work_items_organize.plan_organization(root)
            self.assertEqual(plan.inspected[0].skipped_reason, "no reliable WI-* id")

    def test_apply_writes_and_moves(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            path = root / "project/work_items/WI-DONE-1.md"
            path.parent.mkdir(parents=True)
            path.write_text("done and completed", encoding="utf-8")
            plan = work_items_organize.plan_organization(root)
            work_items_organize.apply_plan(plan)
            moved = root / "project/work_items/resolved/WI-DONE-1.md"
            self.assertTrue(moved.exists())
            self.assertIn("status: resolved", moved.read_text(encoding="utf-8"))
            self.assertFalse(path.exists())

    def test_replaces_invalid_frontmatter_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            path = root / "project/work_items/WI-STATE-1.md"
            path.parent.mkdir(parents=True)
            content = (
                "---\n"
                "id: WI-STATE-1\n"
                "status: blocked\n"
                "owner: team-a\n"
                "---\n\n"
                "In progress."
            )
            path.write_text(
                content,
                encoding="utf-8",
            )
            plan = work_items_organize.plan_organization(root)
            work_items_organize.apply_plan(plan)
            moved = root / "project/work_items/active/WI-STATE-1.md"
            text = moved.read_text(encoding="utf-8")
            self.assertEqual(text.count("status:"), 1)
            self.assertIn("status: active", text)
            self.assertIn("owner: team-a", text)

    def test_uses_existing_bucket_when_status_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            path = root / "project/work_items/active/WI-BUCKET-1.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                "---\nid: WI-BUCKET-1\n---\n\nPlanned text",
                encoding="utf-8",
            )
            plan = work_items_organize.plan_organization(root)
            item = plan.inspected[0]
            self.assertEqual(item.inferred_status, "active")
            self.assertEqual(item.target, path)

    def test_renames_file_to_match_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            path = root / "project/work_items/notes.md"
            path.parent.mkdir(parents=True)
            path.write_text("# WI-NAME-1\n\nin progress", encoding="utf-8")
            plan = work_items_organize.plan_organization(root)
            item = plan.inspected[0]
            self.assertEqual(item.target.name, "WI-NAME-1.md")

    def test_collision_marks_blocking_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            flat = root / "project/work_items/WI-COLLIDE-1.md"
            bucketed = root / "project/work_items/active/WI-COLLIDE-1.md"
            flat.parent.mkdir(parents=True)
            bucketed.parent.mkdir(parents=True)
            flat.write_text("# WI-COLLIDE-1\n\nin progress", encoding="utf-8")
            bucketed.write_text("# WI-COLLIDE-1\n\nin progress", encoding="utf-8")
            plan = work_items_organize.plan_organization(root)
            with self.assertRaises(ValueError):
                work_items_organize.apply_plan(plan)

    def test_missing_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan = work_items_organize.plan_organization(pathlib.Path(tmp))
            self.assertEqual(len(plan.inspected), 0)
