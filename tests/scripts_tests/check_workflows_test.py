import importlib.util
import os
import pathlib
import subprocess
import tempfile
import unittest


@unittest.skipUnless(
    importlib.util.find_spec("yaml") is not None,
    "PyYAML is required for scripts/check-workflows tests",
)
class CheckWorkflowsScriptTests(unittest.TestCase):
    def _repo_root(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parents[2]

    def _script_path(self) -> pathlib.Path:
        return self._repo_root() / "scripts" / "check-workflows"

    def _run_script_in_workspace(
        self, workspace: pathlib.Path
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(self._script_path())],
            check=False,
            capture_output=True,
            text=True,
            cwd=workspace,
            env=os.environ.copy(),
        )

    def test_check_workflows_reports_ok_for_valid_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = pathlib.Path(temp_dir)
            workflows_dir = workspace / ".github" / "workflows"
            workflows_dir.mkdir(parents=True)
            (workflows_dir / "valid.yml").write_text(
                "name: Valid\non:\n  workflow_dispatch:\n",
                encoding="utf-8",
            )

            completed = self._run_script_in_workspace(workspace)

        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        self.assertIn("OK: .github/workflows/valid.yml", completed.stdout)

    def test_check_workflows_reports_error_for_invalid_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = pathlib.Path(temp_dir)
            workflows_dir = workspace / ".github" / "workflows"
            workflows_dir.mkdir(parents=True)
            (workflows_dir / "broken.yml").write_text(
                "name: Broken\non: [\n",
                encoding="utf-8",
            )

            completed = self._run_script_in_workspace(workspace)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("ERROR: .github/workflows/broken.yml", completed.stdout)

    def test_check_workflows_fails_when_any_file_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = pathlib.Path(temp_dir)
            workflows_dir = workspace / ".github" / "workflows"
            workflows_dir.mkdir(parents=True)
            (workflows_dir / "valid.yml").write_text(
                "name: Valid\non:\n  workflow_dispatch:\n",
                encoding="utf-8",
            )
            (workflows_dir / "broken.yaml").write_text(
                "name: Broken\non: [\n",
                encoding="utf-8",
            )

            completed = self._run_script_in_workspace(workspace)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("OK: .github/workflows/valid.yml", completed.stdout)
        self.assertIn("ERROR: .github/workflows/broken.yaml", completed.stdout)


if __name__ == "__main__":
    unittest.main()
