import os
import pathlib
import subprocess
import sys
import tempfile
import unittest


class ProjectDoctorCliTest(unittest.TestCase):
    def _repo_root(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parents[2]

    def _run(
        self, args: list[str], cwd: pathlib.Path
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "lrh.cli.main", *args],
            check=False,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            cwd=cwd,
        )

    def test_empty_repository_reports_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            completed = self._run(
                ["project", "doctor", "--project-root", str(root)],
                cwd=self._repo_root(),
            )
            self.assertEqual(completed.returncode, 1, msg=completed.stderr)
            self.assertIn("missing required path: project", completed.stdout)
            self.assertIn("lrh project init --profile prompt-workflow", completed.stdout)

    def test_minimal_bootstrap_has_warnings_but_no_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            init_completed = self._run(
                [
                    "project",
                    "init",
                    "--profile",
                    "minimal",
                    "--project-root",
                    str(root),
                ],
                cwd=self._repo_root(),
            )
            self.assertEqual(init_completed.returncode, 0, msg=init_completed.stderr)

            completed = self._run(
                ["project", "doctor", "--project-root", str(root)],
                cwd=self._repo_root(),
            )
            self.assertEqual(completed.returncode, 1, msg=completed.stderr)
            self.assertIn("WARNING", completed.stdout)

    def test_prompt_workflow_bootstrap_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            self._run(
                [
                    "project",
                    "init",
                    "--profile",
                    "full",
                    "--project-root",
                    str(root),
                ],
                cwd=self._repo_root(),
            )
            scripts = root / "scripts"
            scripts.mkdir(exist_ok=True)
            for name in ("test", "lint", "format"):
                (scripts / name).write_text("#!/usr/bin/env bash\n", encoding="utf-8")

            completed = self._run(
                ["project", "doctor", "--project-root", str(root)],
                cwd=self._repo_root(),
            )
            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            self.assertNotIn("ERROR", completed.stdout)

    def test_strict_returns_nonzero_on_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            self._run(
                [
                    "project",
                    "init",
                    "--profile",
                    "full",
                    "--project-root",
                    str(root),
                ],
                cwd=self._repo_root(),
            )
            completed = self._run(
                ["project", "doctor", "--project-root", str(root), "--strict"],
                cwd=self._repo_root(),
            )
            self.assertEqual(completed.returncode, 1, msg=completed.stderr)

    def test_json_output_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            completed = self._run(
                ["project", "doctor", "--project-root", str(root), "--json"],
                cwd=self._repo_root(),
            )
            self.assertEqual(completed.returncode, 1, msg=completed.stderr)
            self.assertIn('"findings"', completed.stdout)


if __name__ == "__main__":
    unittest.main()
