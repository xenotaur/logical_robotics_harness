import tempfile
import unittest
from pathlib import Path

from lrh.assist import snapshot_cli


class TestSnapshotCliWorkItemDiscovery(unittest.TestCase):
    def test_list_work_items_excludes_non_work_item_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir) / "project"
            (project_dir / "work_items" / "active").mkdir(parents=True)
            (project_dir / "work_items").mkdir(parents=True, exist_ok=True)
            (project_dir / "work_items" / "README.md").write_text(
                "# Work Items\n",
                encoding="utf-8",
            )
            target = project_dir / "work_items" / "active" / "WI-0001.md"
            target.write_text(
                (
                    "---\n"
                    "id: WI-0001\n"
                    "title: Example\n"
                    "type: deliverable\n"
                    "status: active\n"
                    "---\n"
                ),
                encoding="utf-8",
            )

            result = snapshot_cli.list_work_items(project_dir)

            self.assertEqual(result, [target])


if __name__ == "__main__":
    unittest.main()
