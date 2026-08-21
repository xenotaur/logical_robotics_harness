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

    def test_export_reports_oserror_cleanly(self) -> None:
        """Regression test: export's CLI handler previously caught only
        MemoryValidationError, so an --output path that can't be created
        (e.g. its parent is actually a file) surfaced an uncaught
        traceback instead of a clean error: ... message."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            blocking_file = pathlib.Path(tmp) / "not-a-directory"
            blocking_file.write_text("x", encoding="utf-8")

            self._run(
                "write",
                "feedback-export-oserror",
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
                "export",
                "--output",
                str(blocking_file / "bundle.jsonl"),
                "--name",
                "feedback-export-oserror",
                "--project-root",
                str(project_root),
                "--claude-projects-root",
                str(claude_root),
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("error:", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_export_requires_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"

            self._run(
                "write",
                "feedback-export-target",
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
                "export",
                "--output",
                str(pathlib.Path(tmp) / "bundle.jsonl"),
                "--project-root",
                str(project_root),
                "--claude-projects-root",
                str(claude_root),
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("explicit --name or --agent filter", result.stderr)

    def test_export_then_import_then_transfer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            source_root = pathlib.Path(tmp) / "proj_a"
            dest_root = pathlib.Path(tmp) / "proj_b"
            transfer_root = pathlib.Path(tmp) / "proj_c"
            bundle_path = pathlib.Path(tmp) / "bundle.jsonl"

            self._run(
                "write",
                "feedback-portable",
                "--description",
                "d",
                "--type",
                "feedback",
                "--agent",
                "claude",
                "--project-root",
                str(source_root),
                "--claude-projects-root",
                str(claude_root),
                input_text="body text\n",
            )

            export_result = self._run(
                "export",
                "--output",
                str(bundle_path),
                "--name",
                "feedback-portable",
                "--project-root",
                str(source_root),
                "--claude-projects-root",
                str(claude_root),
            )
            self.assertEqual(export_result.returncode, 0, msg=export_result.stderr)
            self.assertIn("exported: 1", export_result.stdout)
            self.assertTrue(bundle_path.exists())

            import_result = self._run(
                "import",
                "--input",
                str(bundle_path),
                "--project-root",
                str(dest_root),
                "--claude-projects-root",
                str(claude_root),
            )
            self.assertEqual(import_result.returncode, 0, msg=import_result.stderr)
            self.assertIn("import complete: 1 written, 0 errors", import_result.stdout)

            list_result = self._run(
                "list",
                "--project-root",
                str(dest_root),
                "--claude-projects-root",
                str(claude_root),
            )
            self.assertIn("feedback_portable.md", list_result.stdout)

            transfer_result = self._run(
                "transfer",
                "--from",
                str(source_root),
                "--to",
                str(transfer_root),
                "--name",
                "feedback-portable",
                "--claude-projects-root",
                str(claude_root),
            )
            self.assertEqual(transfer_result.returncode, 0, msg=transfer_result.stderr)
            self.assertIn(
                "import complete: 1 written, 0 errors", transfer_result.stdout
            )

            transfer_list_result = self._run(
                "list",
                "--project-root",
                str(transfer_root),
                "--claude-projects-root",
                str(claude_root),
            )
            self.assertIn("feedback_portable.md", transfer_list_result.stdout)

    def test_import_dry_run_reports_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            source_root = pathlib.Path(tmp) / "proj_a"
            dest_root = pathlib.Path(tmp) / "proj_b"
            bundle_path = pathlib.Path(tmp) / "bundle.jsonl"

            self._run(
                "write",
                "feedback-dry",
                "--description",
                "d",
                "--type",
                "feedback",
                "--agent",
                "claude",
                "--project-root",
                str(source_root),
                "--claude-projects-root",
                str(claude_root),
                input_text="body\n",
            )
            self._run(
                "export",
                "--output",
                str(bundle_path),
                "--name",
                "feedback-dry",
                "--project-root",
                str(source_root),
                "--claude-projects-root",
                str(claude_root),
            )

            result = self._run(
                "import",
                "--input",
                str(bundle_path),
                "--project-root",
                str(dest_root),
                "--claude-projects-root",
                str(claude_root),
                "--dry-run",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("dry-run:", result.stdout)

            list_result = self._run(
                "list",
                "--project-root",
                str(dest_root),
                "--claude-projects-root",
                str(claude_root),
            )
            self.assertIn("no memory index found", list_result.stdout)

    def test_import_reports_missing_input_file_cleanly(self) -> None:
        """Regression test: a missing --input file must produce a clean
        error: ... message and exit code 1, not an uncaught traceback --
        unlike export/transfer, import previously had no exception
        handling around its core call at all."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            dest_root = pathlib.Path(tmp) / "proj"

            result = self._run(
                "import",
                "--input",
                str(pathlib.Path(tmp) / "does-not-exist.jsonl"),
                "--project-root",
                str(dest_root),
                "--claude-projects-root",
                str(claude_root),
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("error:", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_read_prints_frontmatter_and_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"

            self._run(
                "write",
                "feedback-read-target",
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
                input_text="a distinctive body line\n",
            )

            result = self._run(
                "read",
                "feedback-read-target",
                "--project-root",
                str(project_root),
                "--claude-projects-root",
                str(claude_root),
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("name: feedback-read-target", result.stdout)
            self.assertIn("a distinctive body line", result.stdout)

    def test_read_missing_memory_reports_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"

            result = self._run(
                "read",
                "feedback-does-not-exist",
                "--project-root",
                str(project_root),
                "--claude-projects-root",
                str(claude_root),
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("error:", result.stderr)

    def test_search_finds_and_reports_no_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"

            self._run(
                "write",
                "feedback-search-target",
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
                input_text="a line about apples\n",
            )

            found = self._run(
                "search",
                "apples",
                "--project-root",
                str(project_root),
                "--claude-projects-root",
                str(claude_root),
            )
            self.assertEqual(found.returncode, 0, msg=found.stderr)
            self.assertIn("matches: 1", found.stdout)
            self.assertIn("feedback-search-target", found.stdout)

            not_found = self._run(
                "search",
                "bananas",
                "--project-root",
                str(project_root),
                "--claude-projects-root",
                str(claude_root),
            )
            self.assertEqual(not_found.returncode, 1)
            self.assertIn("matches: 0", not_found.stdout)

    def test_search_empty_query_returns_exit_code_one(self) -> None:
        """Regression test: search's error exit code must be 1, consistent
        with every other MemoryValidationError handler in this CLI (write,
        read, repair, export, import, transfer) -- not the 2 lrh search's
        own unrelated ValueError convention uses."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"

            result = self._run(
                "search",
                "",
                "--project-root",
                str(project_root),
                "--claude-projects-root",
                str(claude_root),
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("error:", result.stderr)


if __name__ == "__main__":
    unittest.main()
