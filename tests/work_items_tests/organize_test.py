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

    def test_missing_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan = work_items_organize.plan_organization(pathlib.Path(tmp))
            self.assertEqual(len(plan.inspected), 0)
