import os
import pathlib
import subprocess
import sys
import unittest


class TestLrhSnapshotCli(unittest.TestCase):
    def _run_lrh(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        src_path = pathlib.Path("src").resolve()
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            str(src_path) if not existing else f"{src_path}{os.pathsep}{existing}"
        )
        return subprocess.run(
            [sys.executable, "-m", "lrh.cli.main", *args],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )

    def test_lrh_snapshot_help(self) -> None:
        result = self._run_lrh(["snapshot", "--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("lrh snapshot", result.stdout)

    def test_lrh_snapshot_project(self) -> None:
        result = self._run_lrh(["snapshot", "project", "--project-root", "."])
        self.assertEqual(result.returncode, 0)
        self.assertIn("# Project Context Packet", result.stdout)

    def test_lrh_snapshot_invalid_arguments(self) -> None:
        result = self._run_lrh(["snapshot", "work_item"])
        self.assertEqual(result.returncode, 2)
        self.assertIn("work_item_id", result.stderr)


if __name__ == "__main__":
    unittest.main()
