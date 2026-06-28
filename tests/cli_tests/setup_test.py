"""CLI-level tests for `lrh setup`."""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile
import unittest


class SetupCliTest(unittest.TestCase):
    def _repo_root(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parents[2]

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "lrh.cli.main", *args],
            check=False,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            cwd=self._repo_root(),
        )

    def _run_isolated(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run lrh with a temporary HOME so the skills dir starts empty."""
        with tempfile.TemporaryDirectory() as fake_home:
            env = os.environ.copy()
            env["HOME"] = fake_home
            env["USERPROFILE"] = fake_home
            return subprocess.run(
                [sys.executable, "-m", "lrh.cli.main", *args],
                check=False,
                capture_output=True,
                text=True,
                env=env,
                cwd=self._repo_root(),
            )

    def test_setup_help_exits_zero(self) -> None:
        result = self._run("setup", "--help")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("--dry-run", result.stdout)
        self.assertIn("--force", result.stdout)

    def test_setup_dry_run_exits_zero(self) -> None:
        result = self._run_isolated("setup", "--dry-run")
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_setup_dry_run_reports_would_install(self) -> None:
        result = self._run_isolated("setup", "--dry-run")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("would install", result.stdout)

    def test_setup_dry_run_suppresses_restart_note(self) -> None:
        result = self._run_isolated("setup", "--dry-run")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertNotIn("Restart Claude Code", result.stdout)


if __name__ == "__main__":
    unittest.main()
