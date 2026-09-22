import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lrh.conversations import claude_session


class TestResolveCurrentClaudeSessionIdentity(unittest.TestCase):
    def test_session_id_resolves_to_transcript(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app_dir = Path(temp_dir)
            project_dir = app_dir / "projects" / "-some-project"
            project_dir.mkdir(parents=True)
            transcript = project_dir / "sess-abc.jsonl"
            transcript.write_text("{}\n", encoding="utf-8")

            identity = claude_session.resolve_current_claude_session_identity(
                environ={"CLAUDE_CODE_SESSION_ID": "sess-abc"},
                app_data_dir=app_dir,
            )

            self.assertEqual(identity.session_id, "sess-abc")
            self.assertEqual(identity.transcript_path, transcript)
            self.assertIsNone(identity.host_session_id)
            self.assertIsNone(identity.session_transcript)

    def test_host_session_id_is_stripped_and_prefixed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app_dir = Path(temp_dir)
            project_dir = app_dir / "projects" / "-some-project"
            project_dir.mkdir(parents=True)
            (project_dir / "sess-abc.jsonl").write_text("{}\n", encoding="utf-8")

            identity = claude_session.resolve_current_claude_session_identity(
                environ={
                    "CLAUDE_CODE_SESSION_ID": "sess-abc",
                    "CLAUDE_CODE_HOST_SESSION_ID": "local_1111-2222-3333",
                },
                app_data_dir=app_dir,
            )

            self.assertEqual(identity.host_session_id, "1111-2222-3333")
            self.assertEqual(
                identity.session_transcript,
                "claude-app:1111-2222-3333",
            )

    def test_unset_session_id_is_rejected_clearly(self) -> None:
        with self.assertRaisesRegex(
            claude_session.ClaudeSessionIdentityError,
            "CLAUDE_CODE_SESSION_ID is not set",
        ):
            claude_session.resolve_current_claude_session_identity(environ={})

    def test_whitespace_only_session_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            claude_session.ClaudeSessionIdentityError,
            "CLAUDE_CODE_SESSION_ID is not set",
        ):
            claude_session.resolve_current_claude_session_identity(
                environ={"CLAUDE_CODE_SESSION_ID": "  "}
            )

    def test_embedded_whitespace_in_session_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            claude_session.ClaudeSessionIdentityError,
            "must not contain whitespace",
        ):
            claude_session.resolve_current_claude_session_identity(
                environ={"CLAUDE_CODE_SESSION_ID": "sess abc"}
            )

    def test_session_id_with_path_separator_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            claude_session.ClaudeSessionIdentityError,
            "invalid Claude Code session id",
        ):
            claude_session.resolve_current_claude_session_identity(
                environ={"CLAUDE_CODE_SESSION_ID": "sub/dir"}
            )

    def test_missing_transcript_match_fails_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app_dir = Path(temp_dir)
            (app_dir / "projects").mkdir()

            with self.assertRaisesRegex(
                claude_session.ClaudeSessionIdentityError,
                "no transcript file found for session id 'sess-abc'",
            ):
                claude_session.resolve_current_claude_session_identity(
                    environ={"CLAUDE_CODE_SESSION_ID": "sess-abc"},
                    app_data_dir=app_dir,
                )

    def test_ambiguous_transcript_match_fails_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app_dir = Path(temp_dir)
            for name in ("project-a", "project-b"):
                project_dir = app_dir / "projects" / name
                project_dir.mkdir(parents=True)
                (project_dir / "sess-abc.jsonl").write_text("{}\n", encoding="utf-8")

            with self.assertRaisesRegex(
                claude_session.ClaudeSessionIdentityError,
                "multiple transcript files found for session id 'sess-abc'",
            ):
                claude_session.resolve_current_claude_session_identity(
                    environ={"CLAUDE_CODE_SESSION_ID": "sess-abc"},
                    app_data_dir=app_dir,
                )

    def test_isolated_environ_config_dir_is_honored_when_app_data_dir_omitted(
        self,
    ) -> None:
        # CLAUDE_CONFIG_DIR must be read from the supplied `environ`, not
        # the real process environment, when app_data_dir is omitted.
        with tempfile.TemporaryDirectory() as temp_dir:
            app_dir = Path(temp_dir)
            project_dir = app_dir / "projects" / "-some-project"
            project_dir.mkdir(parents=True)
            transcript = project_dir / "sess-abc.jsonl"
            transcript.write_text("{}\n", encoding="utf-8")

            with patch.dict("os.environ", {"CLAUDE_CONFIG_DIR": "/not/used"}):
                identity = claude_session.resolve_current_claude_session_identity(
                    environ={
                        "CLAUDE_CODE_SESSION_ID": "sess-abc",
                        "CLAUDE_CONFIG_DIR": str(app_dir),
                    },
                )

            self.assertEqual(identity.transcript_path, transcript)

    def test_unresolvable_named_user_home_reports_clean_error(self) -> None:
        with self.assertRaisesRegex(
            claude_session.ClaudeSessionIdentityError,
            "could not resolve app data directory",
        ):
            claude_session.resolve_current_claude_session_identity(
                environ={"CLAUDE_CODE_SESSION_ID": "sess-abc"},
                app_data_dir=Path("~missing-user-xyz/.claude"),
            )

    def test_directory_named_like_a_transcript_is_not_matched(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app_dir = Path(temp_dir)
            project_dir = app_dir / "projects" / "-some-project"
            project_dir.mkdir(parents=True)
            (project_dir / "sess-abc.jsonl").mkdir()

            with self.assertRaisesRegex(
                claude_session.ClaudeSessionIdentityError,
                "no transcript file found for session id 'sess-abc'",
            ):
                claude_session.resolve_current_claude_session_identity(
                    environ={"CLAUDE_CODE_SESSION_ID": "sess-abc"},
                    app_data_dir=app_dir,
                )

    def test_never_reads_transcript_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app_dir = Path(temp_dir)
            project_dir = app_dir / "projects" / "-some-project"
            project_dir.mkdir(parents=True)
            transcript = project_dir / "sess-abc.jsonl"
            transcript.write_text("SENSITIVE TRANSCRIPT CONTENT\n", encoding="utf-8")

            identity = claude_session.resolve_current_claude_session_identity(
                environ={"CLAUDE_CODE_SESSION_ID": "sess-abc"},
                app_data_dir=app_dir,
            )

            # Only the path is returned; the dataclass carries no content field.
            self.assertEqual(
                {f.name for f in identity.__dataclass_fields__.values()},
                {"session_id", "transcript_path", "host_session_id"},
            )


class TestRunCurrentClaudeSessionIdCli(unittest.TestCase):
    def _write_transcript(self, app_dir: Path, session_id: str) -> Path:
        project_dir = app_dir / "projects" / "-some-project"
        project_dir.mkdir(parents=True, exist_ok=True)
        transcript = project_dir / f"{session_id}.jsonl"
        transcript.write_text("{}\n", encoding="utf-8")
        return transcript

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_text_output_reports_all_fields(self, mock_stdout: io.StringIO) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app_dir = Path(temp_dir)
            transcript = self._write_transcript(app_dir, "sess-abc")

            with patch.dict(
                "os.environ",
                {
                    "CLAUDE_CODE_SESSION_ID": "sess-abc",
                    "CLAUDE_CODE_HOST_SESSION_ID": "local_deadbeef",
                },
                clear=True,
            ):
                result = claude_session.run_current_claude_session_id_cli(
                    ["--app-data-dir", str(app_dir)],
                    prog="lrh conversation current-claude-session-id",
                )

            self.assertEqual(result, 0)
            output = mock_stdout.getvalue()
            self.assertIn("Session ID: sess-abc", output)
            self.assertIn("Session transcript: claude-app:deadbeef", output)
            self.assertIn(f"Transcript path: {transcript}", output)
            self.assertIn("Exported: no", output)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_json_output_is_metadata_only(self, mock_stdout: io.StringIO) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app_dir = Path(temp_dir)
            self._write_transcript(app_dir, "sess-abc")

            with patch.dict(
                "os.environ", {"CLAUDE_CODE_SESSION_ID": "sess-abc"}, clear=True
            ):
                result = claude_session.run_current_claude_session_id_cli(
                    ["--app-data-dir", str(app_dir), "--format", "json"],
                    prog="lrh conversation current-claude-session-id",
                )

            self.assertEqual(result, 0)
            loaded = json.loads(mock_stdout.getvalue())
            self.assertEqual(loaded["session_id"], "sess-abc")
            self.assertIsNone(loaded["session_transcript"])
            self.assertFalse(loaded["exported"])

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_field_output_selects_one_value(self, mock_stdout: io.StringIO) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app_dir = Path(temp_dir)
            transcript = self._write_transcript(app_dir, "sess-abc")

            with patch.dict(
                "os.environ", {"CLAUDE_CODE_SESSION_ID": "sess-abc"}, clear=True
            ):
                result = claude_session.run_current_claude_session_id_cli(
                    [
                        "--app-data-dir",
                        str(app_dir),
                        "--field",
                        "transcript-path",
                    ],
                    prog="lrh conversation current-claude-session-id",
                )

            self.assertEqual(result, 0)
            self.assertEqual(mock_stdout.getvalue().strip(), str(transcript))

    @patch("sys.stderr", new_callable=io.StringIO)
    def test_unset_session_id_exits_nonzero_with_clear_message(
        self, mock_stderr: io.StringIO
    ) -> None:
        with patch.dict("os.environ", {}, clear=True):
            result = claude_session.run_current_claude_session_id_cli(
                [],
                prog="lrh conversation current-claude-session-id",
            )

        self.assertEqual(result, 2)
        self.assertIn("CLAUDE_CODE_SESSION_ID is not set", mock_stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
