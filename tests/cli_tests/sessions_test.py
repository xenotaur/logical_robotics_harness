import argparse
import contextlib
import io
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
import zipfile

from lrh import sessions_workflow


class SessionsCliTest(unittest.TestCase):
    def _repo_root(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parents[2]

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "lrh.cli.main", "sessions", *args],
            check=False,
            capture_output=True,
            text=True,
            cwd=self._repo_root(),
        )

    def test_sessions_no_subcommand_errors(self) -> None:
        completed = self._run()
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("requires a subcommand", completed.stderr)

    def test_sync_mirrors_transcript_and_reports_no_truncation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_projects_root = pathlib.Path(tmp) / "claude-projects"
            project_dir = claude_projects_root / "-fake-proj"
            project_dir.mkdir(parents=True)
            (project_dir / "child-1.jsonl").write_text('{"sessionId": "child-1"}\n')
            archive_root = pathlib.Path(tmp) / "archive"
            project_root = pathlib.Path(tmp) / "proj"

            completed = self._run(
                "sync",
                "--claude-projects-root",
                str(claude_projects_root),
                "--archive-root",
                str(archive_root),
                "--project-root",
                str(project_root),
            )
            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            self.assertIn("1 transcript(s) mirrored", completed.stdout)
            self.assertTrue(
                (archive_root / "raw" / "-fake-proj" / "child-1.jsonl").exists()
            )

    def test_sync_dry_run_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_projects_root = pathlib.Path(tmp) / "claude-projects"
            project_dir = claude_projects_root / "-fake-proj"
            project_dir.mkdir(parents=True)
            (project_dir / "child-1.jsonl").write_text('{"sessionId": "child-1"}\n')
            archive_root = pathlib.Path(tmp) / "archive"

            completed = self._run(
                "sync",
                "--claude-projects-root",
                str(claude_projects_root),
                "--archive-root",
                str(archive_root),
                "--dry-run",
            )
            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            self.assertIn("dry-run:", completed.stdout)
            self.assertFalse(archive_root.exists())

    def test_sync_dry_run_reports_nested_destination(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_projects_root = pathlib.Path(tmp) / "claude-projects"
            live_project_dir = claude_projects_root / "-live-proj"
            stale_project_dir = claude_projects_root / "-stale-proj"
            nested_dir = stale_project_dir / "child-1" / "tool-results"
            live_project_dir.mkdir(parents=True)
            nested_dir.mkdir(parents=True)
            (live_project_dir / "child-1.jsonl").write_text(
                '{"sessionId": "child-1"}\n'
            )
            (nested_dir / "result.txt").write_text("result\n")
            archive_root = pathlib.Path(tmp) / "archive"

            completed = self._run(
                "sync",
                "--claude-projects-root",
                str(claude_projects_root),
                "--archive-root",
                str(archive_root),
                "--dry-run",
            )

            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            self.assertIn(
                str(
                    archive_root
                    / "raw"
                    / "-live-proj"
                    / "child-1"
                    / "tool-results"
                    / "result.txt"
                ),
                completed.stdout,
            )
            self.assertFalse(archive_root.exists())

    def test_sync_harvests_export_zip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_projects_root = pathlib.Path(tmp) / "claude-projects"
            claude_projects_root.mkdir()
            exports_dir = pathlib.Path(tmp) / "exports"
            exports_dir.mkdir()
            zip_path = exports_dir / "session-export-1.zip"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr(
                    "metadata.json",
                    json.dumps(
                        {
                            "sessionId": "local_host-1",
                            "cliSessionId": "child-1",
                            "branch": "feat/x",
                            "title": "T",
                            "prs": [{"url": "https://example.com/pull/1"}],
                        }
                    ),
                )
            archive_root = pathlib.Path(tmp) / "archive"
            project_root = pathlib.Path(tmp) / "proj"

            completed = self._run(
                "sync",
                "--claude-projects-root",
                str(claude_projects_root),
                "--exports-dir",
                str(exports_dir),
                "--archive-root",
                str(archive_root),
                "--project-root",
                str(project_root),
            )
            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            self.assertIn("1 export(s) harvested", completed.stdout)
            index_path = project_root / "project" / "sessions" / "index.jsonl"
            self.assertIn("host-1", index_path.read_text())

    def test_sync_mirrors_nested_file_without_alias_reconciliation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_projects_root = pathlib.Path(tmp) / "claude-projects"
            project_dir = claude_projects_root / "-fake-proj"
            nested_dir = project_dir / "child-1" / "subagents"
            nested_dir.mkdir(parents=True)
            (project_dir / "child-1.jsonl").write_text('{"sessionId": "child-1"}\n')
            (nested_dir / "sub.jsonl").write_text('{"sessionId": "nested"}\n')
            archive_root = pathlib.Path(tmp) / "archive"
            project_root = pathlib.Path(tmp) / "proj"
            args = argparse.Namespace(
                claude_projects_root=str(claude_projects_root),
                exports_dir=None,
                archive_root=str(archive_root),
                project_root=str(project_root),
                dry_run=False,
            )

            with unittest.mock.patch(
                "lrh.prompt_workflow_sessions.reconcile_child_id_aliases",
                return_value=None,
            ) as reconcile:
                with contextlib.redirect_stdout(io.StringIO()):
                    exit_code = sessions_workflow._run_sync(args)

            self.assertEqual(exit_code, 0)
            self.assertTrue(
                (
                    archive_root
                    / "raw"
                    / "-fake-proj"
                    / "child-1"
                    / "subagents"
                    / "sub.jsonl"
                ).exists()
            )
            reconcile.assert_called_once_with(
                str(project_root),
                project_dir / "child-1.jsonl",
                updated_at=unittest.mock.ANY,
            )

    def test_discover_lists_transcripts_as_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp) / "proj"
            claude_projects_root = pathlib.Path(tmp) / "claude-projects"

            # Compute the real slug so the fixture directory matches what
            # discover will actually look for.
            slug_completed = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "import sys; sys.path.insert(0, 'src'); "
                        "from lrh import prompt_workflow_sessions as pws; "
                        f"print(pws.project_slug_for_path(r'{project_root}'))"
                    ),
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=self._repo_root(),
            )
            slug = slug_completed.stdout.strip()
            project_dir = claude_projects_root / slug
            project_dir.mkdir(parents=True)
            (project_dir / "child-1.jsonl").write_text('{"sessionId": "child-1"}\n')

            completed = self._run(
                "discover",
                "--claude-projects-root",
                str(claude_projects_root),
                "--project-root",
                str(project_root),
                "--format",
                "json",
            )
            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            data = json.loads(completed.stdout)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["child_id"], "child-1")
            self.assertIsNone(data[0]["host_id"])

    def test_link_promotes_child_id_to_session_transcript(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp) / "proj"
            record_path = project_root / "project" / "executions" / "AD_HOC" / "r.md"
            record_path.parent.mkdir(parents=True)
            record_path.write_text(
                "---\n"
                "execution_id: R\n"
                "prompt_id: PROMPT(AD_HOC:R)[2026-01-01T00:00:00+00:00]\n"
                "work_item: AD_HOC\n"
                "status: landed\n"
                "rerun_of:\n"
                "pr:\n"
                "commit:\n"
                "created_at: 2026-01-01T00:00:00+00:00\n"
                "session_transcript: pending\n"
                "---\n\n# Summary\ntest\n",
                encoding="utf-8",
            )

            index_completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "prompt",
                    "record-session-alias",
                    "--host-id",
                    "host-1",
                    "--child-id",
                    "child-1",
                    "--project-root",
                    str(project_root),
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=self._repo_root(),
            )
            self.assertEqual(index_completed.returncode, 0, msg=index_completed.stderr)

            completed = self._run(
                "link",
                "--execution-id",
                "R",
                "--child-id",
                "child-1",
                "--project-root",
                str(project_root),
            )
            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            self.assertIn(
                "session_transcript: claude-app:host-1",
                record_path.read_text(encoding="utf-8"),
            )

    def test_link_unknown_child_id_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp) / "proj"
            completed = self._run(
                "link",
                "--execution-id",
                "R",
                "--child-id",
                "nonexistent",
                "--project-root",
                str(project_root),
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("no session in the index", completed.stderr)

    def test_report_json_is_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp) / "proj"
            archive_root = pathlib.Path(tmp) / "archive"
            record_path = project_root / "project" / "executions" / "WI-TEST" / "r.md"
            record_path.parent.mkdir(parents=True)
            record_path.write_text(
                "---\n"
                "execution_id: R\n"
                "prompt_id: PROMPT(WI-TEST:R)[2026-01-01T00:00:00+00:00]\n"
                "work_item: WI-TEST\n"
                "status: landed\n"
                "rerun_of:\n"
                "pr: https://github.com/x/y/pull/1\n"
                "commit: abc123\n"
                "created_at: 2026-01-01T00:00:00+00:00\n"
                "session_transcript: claude-app:host-1\n"
                "---\n\n# Summary\ntest\n",
                encoding="utf-8",
            )
            index_completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "prompt",
                    "record-session-alias",
                    "--host-id",
                    "host-1",
                    "--child-id",
                    "child-1",
                    "--project-root",
                    str(project_root),
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=self._repo_root(),
            )
            self.assertEqual(index_completed.returncode, 0, msg=index_completed.stderr)
            archived = archive_root / "raw" / "slug" / "child-1.jsonl"
            archived.parent.mkdir(parents=True)
            archived.write_text("RAW TRANSCRIPT SECRET\n", encoding="utf-8")

            completed = self._run(
                "report",
                "--project-root",
                str(project_root),
                "--archive-root",
                str(archive_root),
                "--format",
                "json",
            )

            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            self.assertNotIn("RAW TRANSCRIPT SECRET", completed.stdout)
            data = json.loads(completed.stdout)
            self.assertEqual(data["archived"], 1)
            self.assertEqual(data["dangling"], [])
            self.assertEqual(data["unarchived"], [])

    def test_report_text_lists_unarchived_without_body_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp) / "proj"
            archive_root = pathlib.Path(tmp) / "archive"
            record_path = project_root / "project" / "executions" / "WI-TEST" / "r.md"
            record_path.parent.mkdir(parents=True)
            record_path.write_text(
                "---\n"
                "execution_id: R\n"
                "prompt_id: PROMPT(WI-TEST:R)[2026-01-01T00:00:00+00:00]\n"
                "work_item: WI-TEST\n"
                "status: landed\n"
                "rerun_of:\n"
                "pr: https://github.com/x/y/pull/1\n"
                "commit: abc123\n"
                "created_at: 2026-01-01T00:00:00+00:00\n"
                "session_transcript: claude-app:host-1\n"
                "---\n\n# Summary\ntest\n",
                encoding="utf-8",
            )
            index_completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "prompt",
                    "record-session-alias",
                    "--host-id",
                    "host-1",
                    "--child-id",
                    "child-1",
                    "--project-root",
                    str(project_root),
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=self._repo_root(),
            )
            self.assertEqual(index_completed.returncode, 0, msg=index_completed.stderr)

            completed = self._run(
                "report",
                "--project-root",
                str(project_root),
                "--archive-root",
                str(archive_root),
            )

            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            self.assertIn("session archive report", completed.stdout)
            self.assertIn("unarchived: 1", completed.stdout)
            self.assertIn("R [landed]", completed.stdout)

    def test_report_rejects_invalid_since_created_at(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp) / "proj"
            completed = self._run(
                "report",
                "--project-root",
                str(project_root),
                "--since-created-at",
                "not-a-timestamp",
            )

            self.assertEqual(completed.returncode, 1)
            self.assertIn("since_created_at must be an ISO timestamp", completed.stderr)


if __name__ == "__main__":
    unittest.main()
