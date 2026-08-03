"""CLI-level tests for `lrh skills install`."""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile
import unittest


class SkillsInstallCliTest(unittest.TestCase):
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

    def _run_local(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run lrh with a temporary CWD so --local installs to a clean dir."""
        with tempfile.TemporaryDirectory() as fake_cwd:
            return subprocess.run(
                [sys.executable, "-m", "lrh.cli.main", *args],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
                cwd=fake_cwd,
            )

    def test_skills_install_help_exits_zero(self) -> None:
        result = self._run("skills", "install", "--help")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("--dry-run", result.stdout)
        self.assertIn("--force", result.stdout)
        self.assertIn("--local", result.stdout)
        self.assertIn("--target", result.stdout)

    def test_skills_install_dry_run_exits_zero(self) -> None:
        result = self._run_isolated("skills", "install", "--dry-run")
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_skills_install_dry_run_reports_would_install(self) -> None:
        result = self._run_isolated("skills", "install", "--dry-run")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("would install", result.stdout)

    def test_skills_install_dry_run_suppresses_restart_note(self) -> None:
        result = self._run_isolated("skills", "install", "--dry-run")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertNotIn("Restart Claude Code", result.stdout)

    def test_skills_install_local_dry_run_exits_zero(self) -> None:
        result = self._run_local("skills", "install", "--local", "--dry-run")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("would install", result.stdout)

    def test_skills_install_codex_dry_run_exits_zero(self) -> None:
        result = self._run_isolated(
            "skills", "install", "--target", "codex", "--dry-run"
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("would install", result.stdout)

    def test_skills_install_all_local_dry_run_reports_both_targets(self) -> None:
        result = self._run_local(
            "skills", "install", "--local", "--target", "all", "--dry-run"
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("claude:", result.stdout)
        self.assertIn(".claude/skills", result.stdout)
        self.assertIn("codex:", result.stdout)
        self.assertIn(".agents/skills", result.stdout)

    def test_skills_install_local_codex_writes_agents_skills(self) -> None:
        with tempfile.TemporaryDirectory() as fake_cwd:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "skills",
                    "install",
                    "--local",
                    "--target",
                    "codex",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
                cwd=fake_cwd,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue((pathlib.Path(fake_cwd) / ".agents" / "skills").exists())
            self.assertFalse((pathlib.Path(fake_cwd) / ".claude" / "skills").exists())

    def test_skills_install_local_codex_diff_reports_local_modification(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as fake_cwd:
            env = os.environ.copy()
            install_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "skills",
                    "install",
                    "--local",
                    "--target",
                    "codex",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=env,
                cwd=fake_cwd,
            )
            self.assertEqual(install_result.returncode, 0, msg=install_result.stderr)
            skill_md = next(
                (pathlib.Path(fake_cwd) / ".agents" / "skills").glob("*/SKILL.md")
            )
            skill_md.write_text(skill_md.read_text() + "\n# codex local change\n")

            diff_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "skills",
                    "install",
                    "--local",
                    "--target",
                    "codex",
                    "--diff",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=env,
                cwd=fake_cwd,
            )

            self.assertEqual(diff_result.returncode, 0, msg=diff_result.stderr)
            self.assertIn("warning:", diff_result.stdout)
            self.assertIn("--- diff:", diff_result.stdout)
            self.assertIn("+# codex local change", diff_result.stdout)
            self.assertIn("codex local change", skill_md.read_text())

    def test_skills_install_invalid_target_rejected(self) -> None:
        result = self._run("skills", "install", "--target", "chatgpt", "--dry-run")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid choice", result.stderr)

    def test_setup_command_unrecognized(self) -> None:
        result = self._run("setup")
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
