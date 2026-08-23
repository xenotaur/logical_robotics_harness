"""Unit tests for Antigravity conversation export API."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from lrh.conversations import antigravity_export, export_inspector


def _write_transcript(tmp_path: Path, lines: list[dict | str]) -> Path:
    transcript_file = tmp_path / "transcript.jsonl"
    content_lines: list[str] = []
    for item in lines:
        if isinstance(item, str):
            content_lines.append(item)
        else:
            content_lines.append(json.dumps(item))
    transcript_file.write_text("\n".join(content_lines) + "\n", encoding="utf-8")
    return transcript_file


class TestAntigravityExport(unittest.TestCase):
    def test_convert_antigravity_session_basic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            steps = [
                {
                    "step_index": 0,
                    "source": "USER_EXPLICIT",
                    "type": "USER_INPUT",
                    "status": "DONE",
                    "content": "Hello, please list files.",
                },
                {
                    "step_index": 1,
                    "source": "MODEL",
                    "type": "PLANNER_RESPONSE",
                    "status": "DONE",
                    "thinking": "User wants file listing.",
                    "tool_calls": [
                        {
                            "name": "list_dir",
                            "args": {"DirectoryPath": "/tmp"},
                        }
                    ],
                },
            ]
            source_file = _write_transcript(tmp_path, steps)
            out_file = tmp_path / "export.md"

            res = antigravity_export.convert_antigravity_session(
                source_file,
                output_path=out_file,
                source_id="test_session_123",
                exported_at="2026-08-08T12:00:00Z",
            )

            self.assertTrue(out_file.exists())
            self.assertEqual(res.manifest.source_tool, "antigravity")
            self.assertEqual(
                res.manifest.source_adapter, "antigravity_transcript_jsonl"
            )
            self.assertEqual(res.manifest.kind, "lrh_antigravity_conversation_export")
            self.assertEqual(res.manifest.source_id, "test_session_123")
            self.assertEqual(res.manifest.transcript_statistics.turn_count, 1)
            self.assertIn("## User", res.markdown)
            self.assertIn("Hello, please list files.", res.markdown)
            self.assertIn("## Assistant", res.markdown)
            self.assertIn("Thinking", res.markdown)
            self.assertIn("list_dir", res.markdown)

            # Verify compatibility with inspect_export
            inspection = export_inspector.inspect_export(
                out_file, source_path=source_file
            )
            self.assertTrue(inspection.valid)
            self.assertTrue(inspection.manifest_valid)
            self.assertEqual(inspection.source_hash.status, "match")

    def test_convert_antigravity_session_file_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            missing = tmp_path / "non_existent.jsonl"
            with self.assertRaisesRegex(
                antigravity_export.AntigravityExportError, "does not exist"
            ):
                antigravity_export.convert_antigravity_session(missing)

    def test_convert_antigravity_session_output_collision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            source_file = _write_transcript(
                tmp_path,
                [
                    {
                        "step_index": 0,
                        "source": "USER",
                        "type": "USER_INPUT",
                        "content": "hi",
                    }
                ],
            )
            out_file = tmp_path / "export.md"
            out_file.write_text("existing content", encoding="utf-8")

            with self.assertRaisesRegex(FileExistsError, "already exists"):
                antigravity_export.convert_antigravity_session(
                    source_file, output_path=out_file
                )

            # Force overwrite succeeds
            res = antigravity_export.convert_antigravity_session(
                source_file, output_path=out_file, force=True
            )
            self.assertIn("## User", res.markdown)

    def test_convert_antigravity_session_malformed_lines_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            source_file = _write_transcript(
                tmp_path,
                [
                    {
                        "step_index": 0,
                        "source": "USER",
                        "type": "USER_INPUT",
                        "content": "valid step",
                    },
                    "this is not valid json {{{",
                ],
            )
            res = antigravity_export.convert_antigravity_session(source_file)
            self.assertEqual(len(res.manifest.warnings), 1)
            self.assertIn("line 2: invalid JSON", res.manifest.warnings[0])

    def test_convert_antigravity_session_derive_source_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            nested_dir = (
                tmp_path / "brain" / "sess_abc123" / ".system_generated" / "logs"
            )
            nested_dir.mkdir(parents=True)
            source_file = nested_dir / "transcript.jsonl"
            source_file.write_text(
                json.dumps({"step_index": 0, "source": "USER", "content": "hello"})
                + "\n",
                encoding="utf-8",
            )

            res = antigravity_export.convert_antigravity_session(source_file)
            self.assertEqual(res.manifest.source_id, "sess_abc123")

    def test_cli_convert_antigravity_session_with_transcript_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            source_file = _write_transcript(
                tmp_path,
                [
                    {
                        "step_index": 0,
                        "source": "USER",
                        "type": "USER_INPUT",
                        "content": "test message",
                    }
                ],
            )
            out_file = tmp_path / "cli_export.md"

            stdout_buf = io.StringIO()
            stderr_buf = io.StringIO()
            with (
                contextlib.redirect_stdout(stdout_buf),
                contextlib.redirect_stderr(stderr_buf),
            ):
                code = antigravity_export.run_convert_antigravity_session_cli(
                    [
                        "--transcript-path",
                        str(source_file),
                        "--out",
                        str(out_file),
                        "--source-id",
                        "cli_sess_1",
                    ]
                )

            self.assertEqual(code, 0)
            self.assertTrue(out_file.exists())
            stdout = stdout_buf.getvalue()
            self.assertIn("Exported Antigravity session transcript", stdout)
            self.assertIn("Source ID: cli_sess_1", stdout)
            self.assertIn("Privacy: private", stdout)

    def test_cli_convert_antigravity_session_with_conversation_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            logs_dir = (
                tmp_path / "brain" / "sess_xyz987" / ".system_generated" / "logs"
            )
            logs_dir.mkdir(parents=True)
            transcript_file = logs_dir / "transcript.jsonl"
            transcript_file.write_text(
                json.dumps(
                    {
                        "step_index": 0,
                        "source": "USER",
                        "type": "USER_INPUT",
                        "content": "hello via conversation id",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            out_file = tmp_path / "cid_export.md"

            stdout_buf = io.StringIO()
            stderr_buf = io.StringIO()
            with (
                contextlib.redirect_stdout(stdout_buf),
                contextlib.redirect_stderr(stderr_buf),
            ):
                code = antigravity_export.run_convert_antigravity_session_cli(
                    [
                        "--conversation-id",
                        "sess_xyz987",
                        "--app-data-dir",
                        str(tmp_path),
                        "--out",
                        str(out_file),
                    ]
                )

            self.assertEqual(code, 0)
            self.assertTrue(out_file.exists())
            stdout = stdout_buf.getvalue()
            self.assertIn("Source ID: sess_xyz987", stdout)

    def test_cli_convert_antigravity_session_missing_required_args(self) -> None:
        stderr_buf = io.StringIO()
        with contextlib.redirect_stderr(stderr_buf):
            code = antigravity_export.run_convert_antigravity_session_cli([])
        self.assertEqual(code, 1)
        self.assertIn(
            "one of --transcript-path, --conversation-id, or --latest is required",
            stderr_buf.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()
