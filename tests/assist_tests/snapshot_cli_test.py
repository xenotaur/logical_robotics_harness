import tempfile
import unittest
from pathlib import Path
from unittest import mock

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


class TestSnapshotCliHarnessMetadata(unittest.TestCase):
    def test_resolve_harness_version_returns_unknown_when_unavailable(self) -> None:
        with mock.patch(
            "lrh.version.get_installed_version",
            return_value=None,
        ):
            self.assertEqual(snapshot_cli.resolve_harness_version(), "unknown")

    def test_generate_project_context_includes_harness_metadata_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir) / "project"
            (project_dir / "principles").mkdir(parents=True)
            (project_dir / "goal").mkdir(parents=True)
            (project_dir / "design").mkdir(parents=True)
            (project_dir / "roadmap").mkdir(parents=True)
            (project_dir / "focus").mkdir(parents=True)
            (project_dir / "contributors").mkdir(parents=True)

            (project_dir / "goal" / "project_goal.md").write_text(
                "# Goal\n",
                encoding="utf-8",
            )
            (project_dir / "design" / "design.md").write_text(
                "# Design\n",
                encoding="utf-8",
            )
            (project_dir / "roadmap" / "roadmap.md").write_text(
                "# Roadmap\n",
                encoding="utf-8",
            )
            (project_dir / "focus" / "current_focus.md").write_text(
                "---\nid: FOCUS-1\n---\n# Focus\n",
                encoding="utf-8",
            )
            (project_dir / "contributors" / "contributors.md").write_text(
                "# Contributors\n",
                encoding="utf-8",
            )

            args = snapshot_cli.build_parser(prog="snapshot").parse_args(["project"])
            with mock.patch(
                "lrh.version.get_installed_version",
                return_value="1.2.3",
            ):
                output = snapshot_cli.generate_project_context(project_dir, args)

            self.assertIn("Harness metadata:", output)
            self.assertIn("```yaml", output)
            self.assertIn("harness:", output)
            self.assertIn("name: lrh", output)
            self.assertIn("version: 1.2.3", output)


if __name__ == "__main__":
    unittest.main()
