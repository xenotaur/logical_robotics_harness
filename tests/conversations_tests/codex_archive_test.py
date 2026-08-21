import io
import json
import os
import shlex
import stat
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from lrh.conversations import codex_app_server_export, codex_archive

EXPORTED_AT = datetime(2026, 8, 20, 1, 2, 3, tzinfo=timezone.utc)


class TestCodexArchive(unittest.TestCase):
    def test_resolve_codex_archive_root_reuses_session_archive_root(self) -> None:
        with patch.dict(os.environ, {"LRH_SESSION_ARCHIVE_ROOT": "/tmp/lrh-archive"}):
            self.assertEqual(
                codex_archive.resolve_codex_archive_root(),
                Path("/tmp/lrh-archive/codex"),
            )

    def test_plan_codex_export_paths_uses_date_buckets(self) -> None:
        paths = codex_archive.plan_codex_export_paths(
            thread_id="thread:123",
            archive_root="/tmp/archive",
            exported_at=EXPORTED_AT,
        )

        self.assertEqual(
            paths.directory,
            Path(
                "/tmp/archive/codex/exports/2026/08/"
                "lrh-codex-export-20260820T010203Z-thread-123"
            ),
        )
        self.assertEqual(paths.export_path, paths.directory / "export.md")
        self.assertEqual(paths.raw_path, paths.directory / "raw.json")
        self.assertEqual(paths.attempt_path, paths.directory / "attempt.json")
        self.assertFalse(paths.ephemeral)

    def test_archive_codex_thread_writes_attempt_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            server = _write_fake_server(root)
            wrapper = _write_executable_wrapper(root, server)

            result = codex_archive.archive_codex_thread(
                thread_id="thread-123",
                archive_root=root / "archive",
                exported_at=EXPORTED_AT,
                codex_command=[str(wrapper)],
            )

            attempt = json.loads(result.paths.attempt_path.read_text())
            self.assertEqual(attempt["kind"], "lrh_codex_export_attempt")
            self.assertEqual(attempt["status"], "succeeded")
            self.assertEqual(attempt["thread_id"], "thread-123")
            self.assertEqual(attempt["validation"]["status"], "valid")
            self.assertFalse(attempt["ephemeral"])
            self.assertTrue(result.paths.export_path.exists())
            self.assertTrue(result.paths.raw_path.exists())
            self.assertEqual(
                result.export_result.manifest.exported_at,
                "2026-08-20T01:02:03+00:00",
            )
            self.assertEqual(
                stat.S_IMODE(result.paths.attempt_path.stat().st_mode), 0o600
            )
            self.assertNotIn(
                "Private task text",
                result.paths.attempt_path.read_text(encoding="utf-8"),
            )

    def test_archive_codex_thread_same_second_retry_uses_new_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            server = _write_fake_server(root)

            first = codex_archive.archive_codex_thread(
                thread_id="thread-123",
                archive_root=root / "archive",
                exported_at=EXPORTED_AT,
                codex_command=[sys.executable, str(server)],
            )
            second = codex_archive.archive_codex_thread(
                thread_id="thread-123",
                archive_root=root / "archive",
                exported_at=EXPORTED_AT,
                codex_command=[sys.executable, str(server)],
            )

            self.assertNotEqual(first.paths.directory, second.paths.directory)
            self.assertEqual(
                second.paths.directory.name,
                "lrh-codex-export-20260820T010203Z-thread-123-2",
            )
            first_attempt = json.loads(first.paths.attempt_path.read_text())
            second_attempt = json.loads(second.paths.attempt_path.read_text())
            self.assertEqual(first_attempt["status"], "succeeded")
            self.assertEqual(second_attempt["status"], "succeeded")

    def test_archive_codex_thread_records_failed_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            server = _write_fake_server(root, mode="error")

            with self.assertRaises(codex_app_server_export.CodexAppServerExportError):
                codex_archive.archive_codex_thread(
                    thread_id="thread-123",
                    archive_root=root / "archive",
                    exported_at=EXPORTED_AT,
                    codex_command=[sys.executable, str(server)],
                )

            attempt_path = (
                root
                / "archive"
                / "codex"
                / "exports"
                / "2026"
                / "08"
                / "lrh-codex-export-20260820T010203Z-thread-123"
                / "attempt.json"
            )
            attempt = json.loads(attempt_path.read_text())
            self.assertEqual(attempt["status"], "failed")
            self.assertIn("thread/read failed", attempt["error_summary"])
            self.assertFalse(attempt["files_present"]["export_md"])
            self.assertFalse(attempt["files_present"]["raw_json"])

    def test_archive_codex_thread_scratch_mode_is_explicitly_ephemeral(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            server = _write_fake_server(root)

            result = codex_archive.archive_codex_thread(
                thread_id="thread-123",
                archive_root=root / "archive",
                scratch=True,
                scratch_root=root / "scratch",
                exported_at=EXPORTED_AT,
                codex_command=[sys.executable, str(server)],
            )

            self.assertTrue(result.paths.ephemeral)
            self.assertTrue(
                str(result.paths.directory).startswith(str(root / "scratch"))
            )
            attempt = json.loads(result.paths.attempt_path.read_text())
            self.assertTrue(attempt["ephemeral"])

    def test_import_codex_export_directories_classifies_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            server = _write_fake_server(root)
            source_root = root / "CodexExports"
            valid_source = source_root / "lrh-codex-export-20260820T010203Z.valid"
            empty_source = source_root / "lrh-codex-export-20260820T010204Z.empty"
            partial_source = source_root / "lrh-codex-export-20260820T010205Z.partial"
            valid_source.mkdir(parents=True)
            empty_source.mkdir()
            partial_source.mkdir()
            (partial_source / "export.md").write_text("partial", encoding="utf-8")
            codex_app_server_export.export_codex_thread(
                thread_id="thread-123",
                output_path=valid_source / "export.md",
                raw_output_path=valid_source / "raw.json",
                codex_command=[sys.executable, str(server)],
                exported_at=EXPORTED_AT,
            )
            (valid_source / "export.md").chmod(0o644)

            results = codex_archive.import_codex_export_directories(
                source_root,
                archive_root=root / "archive",
                imported_at=EXPORTED_AT,
            )

            statuses = {result.source.name: result.status for result in results}
            self.assertEqual(
                statuses,
                {
                    valid_source.name: "imported",
                    empty_source.name: "empty",
                    partial_source.name: "partial",
                },
            )
            for result in results:
                self.assertIsNotNone(result.destination)
                assert result.destination is not None
                attempt = json.loads(
                    (result.destination / "attempt.json").read_text(encoding="utf-8")
                )
                self.assertEqual(attempt["operation"], "import")
                self.assertEqual(attempt["status"], result.status)
                if result.status == "imported":
                    self.assertEqual(
                        stat.S_IMODE((result.destination / "export.md").stat().st_mode),
                        0o600,
                    )

    def test_import_rejects_archive_root_inside_git_worktree(self) -> None:
        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            worktree = root / "worktree"
            worktree.mkdir()
            (worktree / ".git").mkdir()
            source_root = root / "CodexExports"
            (source_root / "lrh-codex-export-20260820T010203Z.empty").mkdir(
                parents=True
            )
            os.chdir(worktree)
            try:
                with self.assertRaisesRegex(
                    codex_archive.CodexArchiveError,
                    "archive root must be outside the current Git worktree",
                ):
                    codex_archive.import_codex_export_directories(
                        source_root,
                        archive_root=worktree / "private",
                        imported_at=EXPORTED_AT,
                    )
            finally:
                os.chdir(original_cwd)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_import_cli_is_metadata_only(self, mock_stdout: io.StringIO) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            server = _write_fake_server(root)
            source = root / "lrh-codex-export-20260820T010203Z.valid"
            source.mkdir()
            codex_app_server_export.export_codex_thread(
                thread_id="thread-123",
                output_path=source / "export.md",
                raw_output_path=source / "raw.json",
                codex_command=[sys.executable, str(server)],
                exported_at=EXPORTED_AT,
            )

            exit_code = codex_archive.run_import_codex_exports_cli(
                [str(source), "--archive-root", str(root / "archive")],
                prog="lrh conversation import-codex-exports",
            )

            output = mock_stdout.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("imported:", output)
            self.assertIn("import summary:", output)
            self.assertNotIn("Private task text", output)
            self.assertNotIn("Private response text", output)


def _write_fake_server(root: Path, *, mode: str = "success") -> Path:
    thread = {
        "id": "thread-123",
        "name": "Archive task",
        "status": {"type": "completed"},
        "turns": [
            {
                "id": "turn-1",
                "status": "completed",
                "startedAt": "2026-08-20T01:02:00Z",
                "completedAt": "2026-08-20T01:02:01Z",
                "items": [
                    {"type": "userMessage", "text": "Private task text"},
                    {
                        "type": "agentMessage",
                        "phase": "final_answer",
                        "content": [{"text": "Private response text"}],
                    },
                ],
            }
        ],
    }
    script = root / f"fake_codex_archive_{mode}.py"
    script.write_text(
        f"""\
import json
import sys

THREAD = {json.dumps(thread, sort_keys=True)!r}
MODE = {mode!r}


def emit(payload):
    print(json.dumps(payload, sort_keys=True), flush=True)


for raw_line in sys.stdin:
    request = json.loads(raw_line)
    method = request.get("method")
    request_id = request.get("id")
    if method == "initialize":
        emit({{"jsonrpc": "2.0", "id": request_id, "result": {{"ok": True}}}})
    elif method == "initialized":
        continue
    elif method == "thread/read":
        if MODE == "error":
            emit({{
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {{"code": -32000, "message": "thread missing"}},
            }})
        else:
            emit({{
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {{"thread": json.loads(THREAD)}},
            }})
""",
        encoding="utf-8",
    )
    return script


def _write_executable_wrapper(root: Path, server: Path) -> Path:
    wrapper = root / "fake-codex"
    wrapper.write_text(
        "#!/bin/sh\n"
        f'exec {shlex.quote(sys.executable)} {shlex.quote(str(server))} "$@"\n',
        encoding="utf-8",
    )
    wrapper.chmod(0o755)
    return wrapper


if __name__ == "__main__":
    unittest.main()
