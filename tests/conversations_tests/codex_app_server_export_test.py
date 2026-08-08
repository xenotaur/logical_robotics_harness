import hashlib
import io
import json
import os
import shlex
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lrh.conversations import codex_app_server_export, export_inspector

EXPORTED_AT = "2026-08-08T01:02:03+00:00"


class TestCodexAppServerExport(unittest.TestCase):
    def test_export_codex_thread_writes_private_raw_and_manifest_markdown(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            server = _write_fake_server(root)
            output_path = root / "export.md"
            raw_path = root / "raw.json"

            result = codex_app_server_export.export_codex_thread(
                thread_id="thread-123",
                output_path=output_path,
                raw_output_path=raw_path,
                codex_command=[sys.executable, str(server)],
                exported_at=EXPORTED_AT,
            )

            raw_bytes = raw_path.read_bytes()
            raw_capture = json.loads(raw_bytes)
            markdown = output_path.read_text(encoding="utf-8")
            inspection = export_inspector.inspect_export(
                output_path,
                source_path=raw_path,
            )

            self.assertEqual(result.raw_sha256, hashlib.sha256(raw_bytes).hexdigest())
            self.assertEqual(
                raw_capture["capture_kind"], "lrh_codex_app_server_thread_read_capture"
            )
            self.assertEqual(raw_capture["app_server_method"], "thread/read")
            self.assertEqual(raw_capture["request"]["includeTurns"], True)
            self.assertTrue(markdown.startswith("---\n"))
            self.assertIn('source_adapter: "codex_app_server_thread_read"', markdown)
            self.assertIn('source_id: "thread-123"', markdown)
            self.assertIn("### User\n\nPlease export this task.", markdown)
            self.assertIn(
                "### Assistant\n\n- Phase: final_answer\n\nExport complete.", markdown
            )
            self.assertIn("_Reasoning content omitted", markdown)
            self.assertNotIn("private chain of thought", markdown)
            self.assertNotIn("raw file diff secret", markdown)
            self.assertNotIn("summary could include raw details", markdown)
            self.assertNotIn("web summary could include raw result details", markdown)
            self.assertNotIn("prior turns compacted", markdown)
            self.assertTrue(inspection.valid, inspection.errors)
            self.assertEqual(inspection.source_hash.status, "match")
            self.assertEqual(result.manifest.transcript_statistics.turn_count, 2)
            self.assertEqual(result.manifest.transcript_statistics.message_count, 2)
            self.assertEqual(result.item_type_counts["agentMessage"], 1)
            self.assertEqual(result.item_type_counts["fileChange"], 1)
            self.assertIn("codex_trust_state_unverified", result.manifest.warnings)
            self.assertIn("reasoning_items_omitted", result.manifest.warnings)
            self.assertIn("file_change_metadata_only", result.manifest.warnings)
            self.assertIn("web_search_metadata_only", result.manifest.warnings)
            self.assertIn("context_compaction_present", result.manifest.warnings)
            self.assertIn("unknown_item_type_newItem", result.manifest.warnings)
            self.assertEqual(stat.S_IMODE(raw_path.stat().st_mode), 0o600)

    def test_export_codex_thread_rejects_output_collision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "same.md"

            with self.assertRaisesRegex(
                codex_app_server_export.CodexAppServerExportError,
                "different files",
            ):
                codex_app_server_export.export_codex_thread(
                    thread_id="thread-123",
                    output_path=output_path,
                    raw_output_path=output_path,
                    codex_command=[sys.executable, "-c", ""],
                )

    def test_export_codex_thread_rejects_existing_outputs_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_path = root / "export.md"
            raw_path = root / "raw.json"
            output_path.write_text("existing", encoding="utf-8")

            with self.assertRaisesRegex(
                codex_app_server_export.CodexAppServerExportError,
                "already exists",
            ):
                codex_app_server_export.export_codex_thread(
                    thread_id="thread-123",
                    output_path=output_path,
                    raw_output_path=raw_path,
                    codex_command=[sys.executable, "-c", ""],
                )

    def test_json_rpc_error_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            server = _write_fake_server(root, mode="error")

            with self.assertRaisesRegex(
                codex_app_server_export.CodexAppServerExportError,
                "thread/read failed",
            ):
                codex_app_server_export.export_codex_thread(
                    thread_id="thread-123",
                    output_path=root / "export.md",
                    raw_output_path=root / "raw.json",
                    codex_command=[sys.executable, str(server)],
                )

    def test_malformed_app_server_response_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            server = _write_fake_server(root, mode="malformed")

            with self.assertRaisesRegex(
                codex_app_server_export.CodexAppServerExportError,
                "malformed JSON",
            ):
                codex_app_server_export.export_codex_thread(
                    thread_id="thread-123",
                    output_path=root / "export.md",
                    raw_output_path=root / "raw.json",
                    codex_command=[sys.executable, str(server)],
                )

    def test_non_utf8_app_server_response_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            server = _write_fake_server(root, mode="non_utf8")

            with self.assertRaisesRegex(
                codex_app_server_export.CodexAppServerExportError,
                "non-UTF-8 output",
            ):
                codex_app_server_export.export_codex_thread(
                    thread_id="thread-123",
                    output_path=root / "export.md",
                    raw_output_path=root / "raw.json",
                    codex_command=[sys.executable, str(server)],
                )

    def test_app_server_timeout_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            server = _write_fake_server(root, mode="timeout")

            with self.assertRaisesRegex(
                codex_app_server_export.CodexAppServerExportError,
                "timed out waiting for app-server response",
            ):
                codex_app_server_export.export_codex_thread(
                    thread_id="thread-123",
                    output_path=root / "export.md",
                    raw_output_path=root / "raw.json",
                    codex_command=[sys.executable, str(server)],
                    timeout_seconds=0.1,
                )

    def test_app_server_exit_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            server = _write_fake_server(root, mode="exit")

            with self.assertRaisesRegex(
                codex_app_server_export.CodexAppServerExportError,
                "app-server exited before response",
            ):
                codex_app_server_export.export_codex_thread(
                    thread_id="thread-123",
                    output_path=root / "export.md",
                    raw_output_path=root / "raw.json",
                    codex_command=[sys.executable, str(server)],
                )

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_run_export_codex_thread_cli_is_metadata_only(
        self,
        mock_stdout: io.StringIO,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            server = _write_fake_server(root)
            wrapper = _write_executable_wrapper(root, server)
            output_path = root / "export.md"
            raw_path = root / "raw.json"

            result = codex_app_server_export.run_export_codex_thread_cli(
                [
                    "--thread-id",
                    "thread-123",
                    "--out",
                    str(output_path),
                    "--raw-out",
                    str(raw_path),
                    "--codex",
                    str(wrapper),
                ],
                prog="lrh conversation export-codex-thread",
            )

            output = mock_stdout.getvalue()
            self.assertEqual(result, 0)
            self.assertIn(f"Exported Codex thread: {output_path}", output)
            self.assertIn(f"Raw capture: {raw_path}", output)
            self.assertIn("Privacy: private", output)
            self.assertIn("Item types: agentMessage=1", output)
            self.assertIn("Source SHA-256:", output)
            self.assertNotIn("Please export this task", output)
            self.assertNotIn("Export complete", output)

    @patch("sys.stderr", new_callable=io.StringIO)
    def test_run_export_codex_thread_cli_requires_thread_id(
        self,
        mock_stderr: io.StringIO,
    ) -> None:
        with patch.dict(os.environ, {"CODEX_THREAD_ID": ""}):
            result = codex_app_server_export.run_export_codex_thread_cli(
                ["--out", "export.md", "--raw-out", "raw.json"],
                prog="lrh conversation export-codex-thread",
            )

        self.assertEqual(result, 2)
        self.assertIn(
            "--thread-id or CODEX_THREAD_ID is required", mock_stderr.getvalue()
        )

    def test_write_private_bytes_tolerates_missing_fchmod(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "raw.json"

            with patch.object(
                codex_app_server_export.os,
                "fchmod",
                side_effect=AttributeError,
            ):
                codex_app_server_export._write_private_bytes(output_path, b"raw")

            self.assertEqual(output_path.read_bytes(), b"raw")


def _write_fake_server(root: Path, *, mode: str = "success") -> Path:
    thread = {
        "id": "thread-123",
        "name": "Export task",
        "status": {"type": "completed"},
        "turns": [
            {
                "id": "turn-1",
                "status": "completed",
                "startedAt": "2026-08-08T00:00:00Z",
                "completedAt": "2026-08-08T00:00:01Z",
                "items": [
                    {"type": "userMessage", "text": "Please export this task."},
                    {
                        "type": "agentMessage",
                        "phase": "final_answer",
                        "content": [{"text": "Export complete."}],
                    },
                    {"type": "reasoning", "text": "private chain of thought"},
                    {
                        "type": "fileChange",
                        "path": "src/example.py",
                        "status": "modified",
                        "summary": "summary could include raw details",
                        "content": "raw file diff secret",
                    },
                ],
            },
            {
                "id": "turn-2",
                "status": "interrupted",
                "items": [
                    {
                        "type": "webSearch",
                        "query": "Codex app-server docs",
                        "summary": "web summary could include raw result details",
                    },
                    {"type": "contextCompaction", "summary": "prior turns compacted"},
                    {"type": "newItem", "value": "new shape"},
                ],
            },
        ],
    }
    script = root / f"fake_codex_{mode}.py"
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
        elif MODE == "malformed":
            print("{{not json", flush=True)
        elif MODE == "non_utf8":
            sys.stdout.buffer.write(b"\\xff\\n")
            sys.stdout.buffer.flush()
        elif MODE == "timeout":
            continue
        elif MODE == "exit":
            sys.exit(9)
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
