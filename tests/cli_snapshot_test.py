import pathlib
import subprocess
import tempfile
import unittest


class TestLrhSnapshotCli(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = pathlib.Path(__file__).resolve().parents[1]

    def _run_lrh(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            return subprocess.run(
                ["lrh", *args],
                check=False,
                capture_output=True,
                text=True,
                cwd=temp_dir,
            )

    def test_lrh_snapshot_help(self) -> None:
        result = self._run_lrh(["snapshot", "--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("lrh snapshot", result.stdout)
        self.assertIn("{project,current_focus,work_item}", result.stdout)

    def test_lrh_snapshot_project(self) -> None:
        result = self._run_lrh(
            ["snapshot", "project", "--project-root", str(self.repo_root)]
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("# Project Context Packet", result.stdout)

    def test_lrh_snapshot_invalid_arguments(self) -> None:
        result = self._run_lrh(["snapshot", "work_item"])
        self.assertEqual(result.returncode, 2)
        self.assertIn("work_item_id", result.stderr)


if __name__ == "__main__":
    unittest.main()
