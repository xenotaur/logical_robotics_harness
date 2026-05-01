import os
import pathlib
import subprocess
import sys
import tempfile
import unittest


class ProjectInitCliTest(unittest.TestCase):
    def _repo_root(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parents[2]

    def _run(self, args: list[str], cwd: pathlib.Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "lrh.cli.main", *args],
            check=False,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            cwd=cwd,
        )

    def test_minimal_profile_creates_project_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            completed = self._run(
                ["project", "init", "--profile", "minimal", "--project-root", str(root)],
                cwd=self._repo_root(),
            )
            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            self.assertTrue((root / "project" / "principles" / "README.md").exists())
            self.assertIn("applied: created=", completed.stdout)

    def test_prompt_workflow_profile_creates_prompts_and_executions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            completed = self._run(
                ["project", "init", "--profile", "prompt-workflow", "--project-root", str(root)],
                cwd=self._repo_root(),
            )
            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            self.assertTrue((root / "PROMPTS.md").exists())
            self.assertTrue((root / "project" / "executions" / "README.md").exists())

    def test_dry_run_does_not_write_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            completed = self._run(
                ["project", "init", "--profile", "full", "--project-root", str(root), "--dry-run"],
                cwd=self._repo_root(),
            )
            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            self.assertIn("CREATE AGENTS.md", completed.stdout)
            self.assertFalse((root / "AGENTS.md").exists())

    def test_no_overwrite_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            prompts = root / "PROMPTS.md"
            prompts.write_text("custom\n", encoding="utf-8")
            completed = self._run(
                ["project", "init", "--profile", "prompt-workflow", "--project-root", str(root)],
                cwd=self._repo_root(),
            )
            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            self.assertIn("UPDATE PROMPTS.md", completed.stdout)
            self.assertEqual(prompts.read_text(encoding="utf-8"), "custom\n")

    def test_force_overwrites_existing_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            prompts = root / "PROMPTS.md"
            prompts.write_text("custom\n", encoding="utf-8")
            completed = self._run(
                [
                    "project",
                    "init",
                    "--profile",
                    "prompt-workflow",
                    "--project-root",
                    str(root),
                    "--force",
                ],
                cwd=self._repo_root(),
            )
            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            self.assertIn("OVERWRITE PROMPTS.md", completed.stdout)
            self.assertNotEqual(prompts.read_text(encoding="utf-8"), "custom\n")

    def test_check_returns_nonzero_when_bootstrap_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            completed = self._run(
                ["project", "init", "--profile", "minimal", "--project-root", str(root), "--check"],
                cwd=self._repo_root(),
            )
            self.assertEqual(completed.returncode, 1, msg=completed.stderr)
            self.assertIn("CREATE", completed.stdout)

    def test_check_returns_zero_when_up_to_date(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            self._run(
                ["project", "init", "--profile", "minimal", "--project-root", str(root)],
                cwd=self._repo_root(),
            )
            completed = self._run(
                ["project", "init", "--profile", "minimal", "--project-root", str(root), "--check"],
                cwd=self._repo_root(),
            )
            self.assertEqual(completed.returncode, 0, msg=completed.stderr)

    def test_check_detects_drifted_file_as_update(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            self._run(
                ["project", "init", "--profile", "prompt-workflow", "--project-root", str(root)],
                cwd=self._repo_root(),
            )
            (root / "PROMPTS.md").write_text("drift\n", encoding="utf-8")
            completed = self._run(
                ["project", "init", "--profile", "prompt-workflow", "--project-root", str(root), "--check"],
                cwd=self._repo_root(),
            )
            self.assertEqual(completed.returncode, 1, msg=completed.stderr)
            self.assertIn("UPDATE PROMPTS.md", completed.stdout)


if __name__ == "__main__":
    unittest.main()
