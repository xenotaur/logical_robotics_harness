"""Unit tests for Claude Code conversation export API."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lrh.conversations import claude_export, export_inspector, export_manifest


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )


def _user_record(text: str) -> dict:
    return {"type": "user", "message": {"role": "user", "content": text}}


def _assistant_text_record(text: str) -> dict:
    return {
        "type": "assistant",
        "message": {"role": "assistant", "content": [{"type": "text", "text": text}]},
    }


def _tool_result_user_record(tool_use_id: str, content: str) -> dict:
    return {
        "type": "user",
        "message": {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": content,
                    "is_error": False,
                }
            ],
        },
    }


class TestClaudeExport(unittest.TestCase):
    def test_convert_claude_session_basic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            source_file = tmp_path / "sess-abc123.jsonl"
            _write_jsonl(
                source_file,
                [
                    _user_record("List the files."),
                    _assistant_text_record("Here they are."),
                ],
            )
            out_file = tmp_path / "export.md"

            res = claude_export.convert_claude_session(
                source_file,
                output_path=out_file,
                exported_at="2026-09-11T00:00:00Z",
            )

            self.assertTrue(out_file.exists())
            self.assertEqual(res.manifest.source_tool, "claude_code")
            self.assertEqual(res.manifest.source_adapter, "claude_transcript_jsonl")
            self.assertEqual(res.manifest.kind, "lrh_claude_conversation_export")
            self.assertEqual(res.manifest.source_id, "sess-abc123")
            self.assertEqual(res.manifest.transcript_statistics.turn_count, 1)
            self.assertEqual(res.manifest.transcript_statistics.message_count, 2)
            self.assertIn("## User", res.markdown)
            self.assertIn("List the files.", res.markdown)
            self.assertIn("## Assistant", res.markdown)
            self.assertIn("Here they are.", res.markdown)
            self.assertEqual(out_file.stat().st_mode & 0o777, 0o600)

            inspection = export_inspector.inspect_export(
                out_file, source_path=source_file
            )
            self.assertTrue(inspection.valid)
            self.assertTrue(inspection.manifest_valid)
            self.assertEqual(inspection.source_hash.status, "match")

    def test_convert_claude_session_file_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing.jsonl"
            with self.assertRaisesRegex(
                claude_export.ClaudeExportError, "does not exist"
            ):
                claude_export.convert_claude_session(missing)

    def test_convert_claude_session_output_collision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            source_file = tmp_path / "sess.jsonl"
            _write_jsonl(source_file, [_user_record("hi")])
            out_file = tmp_path / "export.md"
            out_file.write_text("existing content", encoding="utf-8")

            with self.assertRaisesRegex(FileExistsError, "already exists"):
                claude_export.convert_claude_session(source_file, output_path=out_file)

            res = claude_export.convert_claude_session(
                source_file, output_path=out_file, force=True
            )
            self.assertIn("## User", res.markdown)

    def test_convert_claude_session_malformed_line_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            source_file = tmp_path / "sess.jsonl"
            source_file.write_text(
                json.dumps(_user_record("valid step")) + "\nnot valid json {{{\n",
                encoding="utf-8",
            )

            res = claude_export.convert_claude_session(source_file)
            self.assertEqual(len(res.manifest.warnings), 1)
            self.assertIn("line 2: invalid JSON", res.manifest.warnings[0])

    def test_convert_claude_session_skips_queue_operation_and_attachment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            source_file = tmp_path / "sess.jsonl"
            _write_jsonl(
                source_file,
                [
                    {"type": "queue-operation", "operation": "enqueue"},
                    {
                        "type": "attachment",
                        "attachment": {"type": "skill_listing", "content": "..."},
                    },
                    _user_record("hello"),
                ],
            )

            res = claude_export.convert_claude_session(source_file)
            self.assertNotIn("queue-operation", res.markdown)
            self.assertNotIn("skill_listing", res.markdown)
            self.assertIn("## User", res.markdown)

    def test_convert_claude_session_include_system_attachments(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            source_file = tmp_path / "sess.jsonl"
            _write_jsonl(
                source_file,
                [
                    {
                        "type": "attachment",
                        "attachment": {"type": "skill_listing", "content": "x"},
                    },
                ],
            )

            res = claude_export.convert_claude_session(
                source_file, include_system_attachments=True
            )
            self.assertIn("System Attachment (skill_listing)", res.markdown)

    def test_convert_claude_session_ai_title_used_as_heading(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            source_file = tmp_path / "sess.jsonl"
            _write_jsonl(
                source_file,
                [
                    _user_record("hi"),
                    {"type": "ai-title", "aiTitle": "Count scenarios"},
                ],
            )

            res = claude_export.convert_claude_session(source_file)
            self.assertIn("# Count scenarios", res.markdown)

    def test_convert_claude_session_renders_tool_use_and_tool_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            source_file = tmp_path / "sess.jsonl"
            _write_jsonl(
                source_file,
                [
                    {
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "tool_use",
                                    "id": "toolu_1",
                                    "name": "Bash",
                                    "input": {"command": "ls"},
                                }
                            ],
                        },
                    },
                    {
                        "type": "user",
                        "message": {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": "toolu_1",
                                    "content": "README.md\n",
                                    "is_error": False,
                                }
                            ],
                        },
                    },
                ],
            )

            res = claude_export.convert_claude_session(source_file)
            self.assertIn("Tool Call: `Bash`", res.markdown)
            self.assertIn('"command": "ls"', res.markdown)
            self.assertIn("Tool Result", res.markdown)
            self.assertIn("README.md", res.markdown)
            self.assertEqual(res.manifest.transcript_statistics.turn_count, 0)

    def test_turn_count_excludes_tool_result_only_user_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            source_file = tmp_path / "sess.jsonl"
            _write_jsonl(
                source_file,
                [
                    _user_record("List the files."),
                    {
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "tool_use",
                                    "id": "toolu_1",
                                    "name": "Bash",
                                    "input": {"command": "ls"},
                                }
                            ],
                        },
                    },
                    _tool_result_user_record("toolu_1", "README.md\n"),
                    _assistant_text_record("Here they are."),
                    _user_record("Thanks, that's all."),
                ],
            )

            res = claude_export.convert_claude_session(source_file)

            self.assertEqual(res.manifest.transcript_statistics.turn_count, 2)

    def test_convert_claude_session_subagents_referenced_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            source_file = tmp_path / "sess-parent.jsonl"
            _write_jsonl(source_file, [_user_record("dispatch a subagent")])

            subagents_dir = tmp_path / "sess-parent" / "subagents"
            subagents_dir.mkdir(parents=True)
            sub_jsonl = subagents_dir / "agent-abc.jsonl"
            _write_jsonl(sub_jsonl, [_user_record("sub task")])
            sub_meta = subagents_dir / "agent-abc.meta.json"
            sub_meta.write_text(
                json.dumps({"agentType": "general-purpose", "description": "Explore"}),
                encoding="utf-8",
            )

            res = claude_export.convert_claude_session(source_file)
            self.assertIn("## Subagents", res.markdown)
            self.assertIn("agent-abc", res.markdown)
            self.assertIn("general-purpose", res.markdown)
            self.assertIn("Explore", res.markdown)
            self.assertNotIn("sub task", res.markdown)

    def test_convert_claude_session_include_subagents_inlines_transcript(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            source_file = tmp_path / "sess-parent.jsonl"
            _write_jsonl(source_file, [_user_record("dispatch a subagent")])

            subagents_dir = tmp_path / "sess-parent" / "subagents"
            subagents_dir.mkdir(parents=True)
            sub_jsonl = subagents_dir / "agent-abc.jsonl"
            _write_jsonl(sub_jsonl, [_user_record("sub task detail")])

            res = claude_export.convert_claude_session(
                source_file, include_subagents=True
            )
            self.assertIn("Subagent transcript: agent-abc", res.markdown)
            self.assertIn("sub task detail", res.markdown)

    def test_resolve_transcript_path_by_session_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            project_dir = tmp_path / "projects" / "-Users-x-proj"
            project_dir.mkdir(parents=True)
            transcript = project_dir / "sess-xyz.jsonl"
            transcript.write_text("{}\n", encoding="utf-8")

            resolved = claude_export._resolve_transcript_path(
                transcript_path=None,
                session_id="sess-xyz",
                app_data_dir=tmp_path,
                latest=False,
            )
            self.assertEqual(resolved, transcript)

    def test_resolve_transcript_path_session_id_multiple_matches_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            for project in ("proj-a", "proj-b"):
                project_dir = tmp_path / "projects" / project
                project_dir.mkdir(parents=True)
                (project_dir / "sess-dup.jsonl").write_text("{}\n", encoding="utf-8")

            with self.assertRaisesRegex(
                claude_export.ClaudeExportError, "multiple transcript files"
            ):
                claude_export._resolve_transcript_path(
                    transcript_path=None,
                    session_id="sess-dup",
                    app_data_dir=tmp_path,
                    latest=False,
                )

    def test_resolve_transcript_path_latest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            project_dir = tmp_path / "projects" / "proj"
            project_dir.mkdir(parents=True)
            older = project_dir / "older.jsonl"
            newer = project_dir / "newer.jsonl"
            older.write_text("{}\n", encoding="utf-8")
            newer.write_text("{}\n", encoding="utf-8")
            import os
            import time

            now = time.time()
            os.utime(older, (now - 100, now - 100))
            os.utime(newer, (now, now))

            resolved = claude_export._resolve_transcript_path(
                transcript_path=None,
                session_id=None,
                app_data_dir=tmp_path,
                latest=True,
            )
            self.assertEqual(resolved, newer)

    def test_resolve_claude_archive_root_worktree_rejection(self) -> None:
        git_root = claude_export._current_git_worktree_root()
        if git_root is not None:
            with self.assertRaises(claude_export.ClaudeExportError) as cm:
                claude_export.resolve_claude_archive_root(git_root / "sub")
            self.assertIn("outside the current Git worktree", str(cm.exception))

    def test_manifest_supports_claude_source_tool(self) -> None:
        self.assertIn(
            export_manifest.SOURCE_TOOL_CLAUDE_CODE,
            export_manifest.SUPPORTED_SOURCE_TOOLS,
        )
        self.assertIn(export_manifest.KIND_CLAUDE, export_manifest.SUPPORTED_KINDS)

    def test_resolve_transcript_path_session_id_rejects_glob_metacharacters(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            project_dir = tmp_path / "projects" / "proj"
            project_dir.mkdir(parents=True)
            (project_dir / "real-session.jsonl").write_text("{}\n", encoding="utf-8")

            # A session id of "*" must not glob-match an unrelated transcript.
            with self.assertRaisesRegex(
                claude_export.ClaudeExportError, "no transcript file found"
            ):
                claude_export._resolve_transcript_path(
                    transcript_path=None,
                    session_id="*",
                    app_data_dir=tmp_path,
                    latest=False,
                )

    def test_resolve_transcript_path_session_id_rejects_path_separator(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            with self.assertRaisesRegex(
                claude_export.ClaudeExportError, "invalid session id"
            ):
                claude_export._resolve_transcript_path(
                    transcript_path=None,
                    session_id="../escape",
                    app_data_dir=tmp_path,
                    latest=False,
                )

    def test_resolve_transcript_path_session_id_with_literal_glob_characters(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            project_dir = tmp_path / "projects" / "proj"
            project_dir.mkdir(parents=True)
            sid = "sess[1]"
            (project_dir / f"{sid}.jsonl").write_text("{}\n", encoding="utf-8")

            resolved = claude_export._resolve_transcript_path(
                transcript_path=None,
                session_id=sid,
                app_data_dir=tmp_path,
                latest=False,
            )
            self.assertEqual(resolved, project_dir / f"{sid}.jsonl")

    def test_tool_result_containing_backticks_does_not_break_fence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            source_file = tmp_path / "sess.jsonl"
            _write_jsonl(
                source_file,
                [
                    {
                        "type": "user",
                        "message": {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": "toolu_1",
                                    "content": "```python\nprint('hi')\n```",
                                    "is_error": False,
                                }
                            ],
                        },
                    },
                ],
            )

            res = claude_export.convert_claude_session(source_file)
            self.assertIn("print('hi')", res.markdown)
            # The wrapping fence must be longer than the content's own
            # embedded triple-backtick run, so the content's "```python"/
            # "```" lines stay nested data rather than closing the block
            # early. The whole original content must therefore appear
            # intact, verbatim, between the (4-backtick) wrapping fences.
            self.assertIn(
                "````\n```python\nprint('hi')\n```\n````",
                res.markdown,
            )

    def test_fenced_code_block_uses_minimum_three_backticks(self) -> None:
        block = claude_export._fenced_code_block("no backticks here")
        self.assertEqual(block[0], "```")
        self.assertEqual(block[2], "```")

    def test_fenced_code_block_extends_past_embedded_run(self) -> None:
        content = "before ```` after"
        block = claude_export._fenced_code_block(content)
        fence = block[0]
        self.assertEqual(fence, "`" * 5)
        self.assertNotIn(fence, content)

    def test_convert_claude_session_rejects_source_output_alias_even_with_force(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            source_file = tmp_path / "sess.jsonl"
            _write_jsonl(source_file, [_user_record("hi")])
            original_content = source_file.read_text(encoding="utf-8")

            with self.assertRaisesRegex(
                claude_export.ClaudeExportError, "must refer to different files"
            ):
                claude_export.convert_claude_session(
                    source_file, output_path=source_file, force=True
                )

            # The source file must be completely untouched.
            self.assertEqual(source_file.read_text(encoding="utf-8"), original_content)

    def test_convert_claude_session_output_file_created_private_from_start(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            source_file = tmp_path / "sess.jsonl"
            _write_jsonl(source_file, [_user_record("hi")])
            out_file = tmp_path / "export.md"

            claude_export.convert_claude_session(source_file, output_path=out_file)

            self.assertEqual(out_file.stat().st_mode & 0o777, 0o600)

    def test_convert_claude_session_propagates_subagent_warnings_when_included(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            source_file = tmp_path / "sess-parent.jsonl"
            _write_jsonl(source_file, [_user_record("dispatch a subagent")])

            subagents_dir = tmp_path / "sess-parent" / "subagents"
            subagents_dir.mkdir(parents=True)
            sub_jsonl = subagents_dir / "agent-broken.jsonl"
            sub_jsonl.write_text(
                json.dumps(_user_record("valid step")) + "\nnot valid json {{{\n",
                encoding="utf-8",
            )

            res = claude_export.convert_claude_session(
                source_file, include_subagents=True
            )
            self.assertTrue(
                any(
                    "agent-broken.jsonl" in warning and "invalid JSON" in warning
                    for warning in res.manifest.warnings
                ),
                res.manifest.warnings,
            )

    def test_convert_claude_session_no_subagent_warnings_when_not_included(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            source_file = tmp_path / "sess-parent.jsonl"
            _write_jsonl(source_file, [_user_record("dispatch a subagent")])

            subagents_dir = tmp_path / "sess-parent" / "subagents"
            subagents_dir.mkdir(parents=True)
            sub_jsonl = subagents_dir / "agent-broken.jsonl"
            sub_jsonl.write_text(
                json.dumps(_user_record("valid step")) + "\nnot valid json {{{\n",
                encoding="utf-8",
            )

            # Referenced-only mode never parses subagent transcripts, so it
            # must never surface their warnings either.
            res = claude_export.convert_claude_session(source_file)
            self.assertEqual(res.manifest.warnings, ())


if __name__ == "__main__":
    unittest.main()
