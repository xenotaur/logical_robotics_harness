import pathlib
import subprocess
import sys
import tempfile
import unittest


class MemoryCliTest(unittest.TestCase):
    def _repo_root(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parents[2]

    def _run(
        self, *args: str, input_text: str | None = None
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "lrh.cli.main", "memory", *args],
            check=False,
            capture_output=True,
            text=True,
            input=input_text,
            cwd=self._repo_root(),
        )

    def test_memory_no_subcommand_errors(self) -> None:
        completed = self._run()
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("requires a subcommand", completed.stderr)

    def test_write_then_list_then_validate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"

            write_result = self._run(
                "write",
                "feedback-cli-test",
                "--description",
                "a cli test memory",
                "--type",
                "feedback",
                "--agent",
                "claude",
                "--project-root",
                str(project_root),
                "--claude-projects-root",
                str(claude_root),
                input_text="test body\n",
            )
            self.assertEqual(write_result.returncode, 0, msg=write_result.stderr)
            self.assertIn("wrote:", write_result.stdout)

            list_result = self._run(
                "list",
                "--project-root",
                str(project_root),
                "--claude-projects-root",
                str(claude_root),
            )
            self.assertEqual(list_result.returncode, 0, msg=list_result.stderr)
            self.assertIn("feedback_cli_test.md", list_result.stdout)

            validate_result = self._run(
                "validate",
                "--project-root",
                str(project_root),
                "--claude-projects-root",
                str(claude_root),
                "--format",
                "json",
            )
            self.assertEqual(validate_result.returncode, 0, msg=validate_result.stderr)
            self.assertIn('"conforming"', validate_result.stdout)
            self.assertIn("feedback_cli_test.md", validate_result.stdout)

    def test_write_rejects_invalid_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            completed = self._run(
                "write",
                "feedback-bad",
                "--description",
                "d",
                "--type",
                "not-a-type",
                "--agent",
                "claude",
                "--project-root",
                str(pathlib.Path(tmp) / "proj"),
                "--claude-projects-root",
                str(pathlib.Path(tmp) / "claude-projects"),
                input_text="body\n",
            )
            self.assertNotEqual(completed.returncode, 0)

    def test_write_second_agent_refused_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"

            self._run(
                "write",
                "feedback-contested",
                "--description",
                "codex's",
                "--type",
                "feedback",
                "--agent",
                "codex",
                "--project-root",
                str(project_root),
                "--claude-projects-root",
                str(claude_root),
                input_text="codex body\n",
            )
            refused = self._run(
                "write",
                "feedback-contested",
                "--description",
                "claude's",
                "--type",
                "feedback",
                "--agent",
                "claude",
                "--project-root",
                str(project_root),
                "--claude-projects-root",
                str(claude_root),
                input_text="claude body\n",
            )
            self.assertEqual(refused.returncode, 1)
            self.assertIn("authored_by 'codex'", refused.stderr)

    def test_repair_preserves_authored_by(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"

            self._run(
                "write",
                "feedback-repair-target",
                "--description",
                "original",
                "--type",
                "feedback",
                "--agent",
                "codex",
                "--project-root",
                str(project_root),
                "--claude-projects-root",
                str(claude_root),
                input_text="body\n",
            )
            repaired = self._run(
                "repair",
                "feedback-repair-target",
                "--set",
                "description=patched",
                "--project-root",
                str(project_root),
                "--claude-projects-root",
                str(claude_root),
            )
            self.assertEqual(repaired.returncode, 0, msg=repaired.stderr)
            self.assertIn("repaired:", repaired.stdout)

    def test_sync_mirrors_then_no_ops_on_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            archive_root = pathlib.Path(tmp) / "archive"

            self._run(
                "write",
                "feedback-sync-target",
                "--description",
                "d",
                "--type",
                "feedback",
                "--agent",
                "claude",
                "--project-root",
                str(project_root),
                "--claude-projects-root",
                str(claude_root),
                input_text="body\n",
            )

            first = self._run(
                "sync",
                "--project-root",
                str(project_root),
                "--claude-projects-root",
                str(claude_root),
                "--archive-root",
                str(archive_root),
            )
            self.assertEqual(first.returncode, 0, msg=first.stderr)
            self.assertIn("sync complete: 2 mirrored, 0 unchanged", first.stdout)
            self.assertTrue((archive_root / "raw").exists())

            second = self._run(
                "sync",
                "--project-root",
                str(project_root),
                "--claude-projects-root",
                str(claude_root),
                "--archive-root",
                str(archive_root),
            )
            self.assertEqual(second.returncode, 0, msg=second.stderr)
            self.assertIn("sync complete: 0 mirrored, 2 unchanged", second.stdout)

    def test_sync_dry_run_reports_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            archive_root = pathlib.Path(tmp) / "archive"

            self._run(
                "write",
                "feedback-sync-dry",
                "--description",
                "d",
                "--type",
                "feedback",
                "--agent",
                "claude",
                "--project-root",
                str(project_root),
                "--claude-projects-root",
                str(claude_root),
                input_text="body\n",
            )

            result = self._run(
                "sync",
                "--project-root",
                str(project_root),
                "--claude-projects-root",
                str(claude_root),
                "--archive-root",
                str(archive_root),
                "--dry-run",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("dry-run:", result.stdout)
            self.assertFalse(archive_root.exists())


if __name__ == "__main__":
    unittest.main()
