"""Unit tests for scripts/test and scripts/validate log redirection flags."""

import os
import pathlib
import subprocess
import sys
import unittest


class ScriptsLogRedirectionTest(unittest.TestCase):
    """Tests for opt-in log redirection in scripts/test and scripts/validate."""

    def setUp(self) -> None:
        self.repo_root = pathlib.Path(__file__).resolve().parents[2]
        self.scripts_dir = self.repo_root / "scripts"
        self.env = dict(
            os.environ,
            PYTHON=sys.executable,
            PYTHONPATH=f"src:{os.environ.get('PYTHONPATH', '')}",
        )

    def test_scripts_test_default_mode(self) -> None:
        """Test scripts/test default mode runs without error on a specific test file."""
        test_file = "tests/control_plane_tests/precedence_test.py"
        proc = subprocess.run(
            [str(self.scripts_dir / "test"), test_file],
            cwd=self.repo_root,
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Testing lrh", proc.stdout)

    def test_scripts_test_log_mode(self) -> None:
        """Test scripts/test --log redirects to tmp/logs/, prints summary."""
        test_file = "tests/control_plane_tests/precedence_test.py"
        proc = subprocess.run(
            [str(self.scripts_dir / "test"), "--log", test_file],
            cwd=self.repo_root,
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("[PASS] Tests completed successfully", proc.stdout)
        self.assertIn("Log: file://", proc.stdout)

    def test_scripts_test_env_var_log_mode(self) -> None:
        """Test LRH_LOG_REDIRECT=1 enables log redirection mode."""
        test_file = "tests/control_plane_tests/precedence_test.py"
        env = dict(self.env, LRH_LOG_REDIRECT="1")
        proc = subprocess.run(
            [str(self.scripts_dir / "test"), test_file],
            cwd=self.repo_root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("[PASS] Tests completed successfully", proc.stdout)
        self.assertIn("Log: file://", proc.stdout)

    def test_scripts_validate_log_mode(self) -> None:
        """Test scripts/validate --log redirects to tmp/logs/, prints summary."""
        proc = subprocess.run(
            [str(self.scripts_dir / "validate"), "--log"],
            cwd=self.repo_root,
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            self.assertIn("[PASS] lrh validate completed successfully", proc.stdout)
            self.assertIn("Log: file://", proc.stdout)
        else:
            self.assertIn("[FAIL] lrh validate failed", proc.stdout)

    def test_scripts_validate_log_mode_under_system_bash(self) -> None:
        """scripts/validate --log works under /bin/bash (3.2 on macOS).

        With no extra arguments, an unguarded empty "${args[@]}" is an
        "unbound variable" error under `set -u` in bash 3.2, so the script
        died before printing its summary line.
        """
        system_bash = pathlib.Path("/bin/bash")
        if not system_bash.exists():
            self.skipTest("no /bin/bash on this platform")
        proc = subprocess.run(
            [str(system_bash), str(self.scripts_dir / "validate"), "--log"],
            cwd=self.repo_root,
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotIn("unbound variable", proc.stderr)
        self.assertRegex(
            proc.stdout, r"\[(PASS|FAIL)\] lrh validate (completed|failed)"
        )


if __name__ == "__main__":
    unittest.main()
