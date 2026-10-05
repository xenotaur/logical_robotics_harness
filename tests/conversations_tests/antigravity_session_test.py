import io
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from lrh.conversations import antigravity_session


class TestAntigravitySessionIdentity(unittest.TestCase):
    def test_explicit_conversation_id_resolves_and_is_trimmed(self) -> None:
        cid = "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d"
        identity = antigravity_session.resolve_antigravity_session_identity(
            f" {cid} ",
            environ={
                antigravity_session.ANTIGRAVITY_CONVERSATION_ID_ENV: (
                    "99999999-9999-9999-9999-999999999999"
                )
            },
        )
        self.assertEqual(identity.conversation_id, cid)
        self.assertEqual(identity.session_transcript, f"antigravity-app:{cid}")
        self.assertFalse(identity.is_latest)

    def test_explicit_conversation_id_finds_transcript_if_present(self) -> None:
        cid = "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d"
        with tempfile.TemporaryDirectory() as tmp:
            app_dir = Path(tmp)
            log_dir = app_dir / "brain" / cid / ".system_generated" / "logs"
            log_dir.mkdir(parents=True)
            transcript_file = log_dir / "transcript.jsonl"
            transcript_file.write_text("{}\n", encoding="utf-8")

            identity = antigravity_session.resolve_antigravity_session_identity(
                cid,
                app_data_dir=app_dir,
                environ={},
            )
            self.assertEqual(identity.conversation_id, cid)
            self.assertEqual(identity.transcript_path, transcript_file)

    def test_explicit_conversation_id_finds_transcript_full_if_present(self) -> None:
        cid = "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d"
        with tempfile.TemporaryDirectory() as tmp:
            app_dir = Path(tmp)
            log_dir = app_dir / "brain" / cid / ".system_generated" / "logs"
            log_dir.mkdir(parents=True)
            transcript_file = log_dir / "transcript_full.jsonl"
            transcript_file.write_text("{}\n", encoding="utf-8")

            identity = antigravity_session.resolve_antigravity_session_identity(
                cid,
                app_data_dir=app_dir,
                environ={},
            )
            self.assertEqual(identity.conversation_id, cid)
            self.assertEqual(identity.transcript_path, transcript_file)

    def test_environment_variable_is_used_when_explicit_missing(self) -> None:
        cid = "12345678-1234-5678-1234-567812345678"
        identity = antigravity_session.resolve_antigravity_session_identity(
            environ={antigravity_session.ANTIGRAVITY_CONVERSATION_ID_ENV: f" {cid} "}
        )
        self.assertEqual(identity.conversation_id, cid)
        self.assertEqual(identity.session_transcript, f"antigravity-app:{cid}")
        self.assertFalse(identity.is_latest)

    def test_malformed_explicit_conversation_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            antigravity_session.AntigravitySessionIdentityError,
            "expected 36-character UUID",
        ):
            antigravity_session.resolve_antigravity_session_identity(
                "not-a-valid-uuid", environ={}
            )

    def test_empty_or_whitespace_explicit_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            antigravity_session.AntigravitySessionIdentityError,
            "must not be empty or whitespace-only",
        ):
            antigravity_session.resolve_antigravity_session_identity("   ", environ={})

    def test_malformed_environment_variable_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            antigravity_session.AntigravitySessionIdentityError,
            "expected 36-character UUID",
        ):
            antigravity_session.resolve_antigravity_session_identity(
                environ={
                    antigravity_session.ANTIGRAVITY_CONVERSATION_ID_ENV: "invalid-uuid"
                }
            )

    def test_missing_environment_and_no_latest_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            antigravity_session.AntigravitySessionIdentityError,
            "ANTIGRAVITY_CONVERSATION_ID is not set",
        ):
            antigravity_session.resolve_antigravity_session_identity(environ={})

    def test_specifying_both_explicit_id_and_latest_is_rejected(self) -> None:
        cid = "12345678-1234-5678-1234-567812345678"
        with self.assertRaisesRegex(
            antigravity_session.AntigravitySessionIdentityError,
            "cannot specify both conversation_id and latest=True",
        ):
            antigravity_session.resolve_antigravity_session_identity(
                cid, latest=True, environ={}
            )

    def test_latest_heuristic_discovers_most_recent_transcript_by_mtime(
        self,
    ) -> None:
        cid_older = "11111111-1111-1111-1111-111111111111"
        cid_newer = "22222222-2222-2222-2222-222222222222"
        with tempfile.TemporaryDirectory() as tmp:
            app_dir = Path(tmp)
            brain_dir = app_dir / "brain"

            log_older = brain_dir / cid_older / ".system_generated" / "logs"
            log_older.mkdir(parents=True)
            f_older = log_older / "transcript.jsonl"
            f_older.write_text("{}\n", encoding="utf-8")

            log_newer = brain_dir / cid_newer / ".system_generated" / "logs"
            log_newer.mkdir(parents=True)
            f_newer = log_newer / "transcript.jsonl"
            f_newer.write_text("{}\n", encoding="utf-8")

            # Set mtime explicitly
            t_now = time.time()
            os.utime(f_older, (t_now - 100, t_now - 100))
            os.utime(f_newer, (t_now, t_now))

            identity = antigravity_session.resolve_antigravity_session_identity(
                latest=True,
                app_data_dir=app_dir,
                environ={},
            )
            self.assertEqual(identity.conversation_id, cid_newer)
            self.assertEqual(
                identity.session_transcript, f"antigravity-app:{cid_newer}"
            )
            self.assertEqual(identity.transcript_path, f_newer)
            self.assertTrue(identity.is_latest)

    def test_latest_fails_when_brain_directory_does_not_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            app_dir = Path(tmp)
            with self.assertRaisesRegex(
                antigravity_session.AntigravitySessionIdentityError,
                "brain directory does not exist",
            ):
                antigravity_session.resolve_antigravity_session_identity(
                    latest=True,
                    app_data_dir=app_dir,
                    environ={},
                )

    def test_latest_fails_when_brain_directory_has_no_transcripts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            app_dir = Path(tmp)
            (app_dir / "brain").mkdir()
            with self.assertRaisesRegex(
                antigravity_session.AntigravitySessionIdentityError,
                "no Antigravity transcript files found",
            ):
                antigravity_session.resolve_antigravity_session_identity(
                    latest=True,
                    app_data_dir=app_dir,
                    environ={},
                )


class TestAntigravitySessionCli(unittest.TestCase):
    def test_cli_resolves_text_format(self) -> None:
        cid = "33333333-3333-3333-3333-333333333333"
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            patch("sys.stdout", stdout),
            patch("sys.stderr", stderr),
            patch.dict(
                os.environ,
                {antigravity_session.ANTIGRAVITY_CONVERSATION_ID_ENV: cid},
                clear=True,
            ),
        ):
            code = antigravity_session.run_current_antigravity_conversation_id_cli([])

        self.assertEqual(code, 0)
        out = stdout.getvalue()
        self.assertIn(f"Conversation ID: {cid}", out)
        self.assertIn(f"Session transcript: antigravity-app:{cid}", out)
        self.assertIn("Exported: no", out)
        self.assertEqual(stderr.getvalue(), "")

    def test_cli_resolves_json_format(self) -> None:
        cid = "33333333-3333-3333-3333-333333333333"
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            patch("sys.stdout", stdout),
            patch("sys.stderr", stderr),
            patch.dict(
                os.environ,
                {antigravity_session.ANTIGRAVITY_CONVERSATION_ID_ENV: cid},
                clear=True,
            ),
        ):
            code = antigravity_session.run_current_antigravity_conversation_id_cli(
                ["--format", "json"]
            )

        self.assertEqual(code, 0)
        data = json.loads(stdout.getvalue())
        self.assertEqual(data["conversation_id"], cid)
        self.assertEqual(data["session_transcript"], f"antigravity-app:{cid}")
        self.assertFalse(data["exported"])

    def test_cli_single_field_session_transcript(self) -> None:
        cid = "33333333-3333-3333-3333-333333333333"
        stdout = io.StringIO()
        with (
            patch("sys.stdout", stdout),
            patch.dict(
                os.environ,
                {antigravity_session.ANTIGRAVITY_CONVERSATION_ID_ENV: cid},
                clear=True,
            ),
        ):
            code = antigravity_session.run_current_antigravity_conversation_id_cli(
                ["--field", "session-transcript"]
            )

        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue().strip(), f"antigravity-app:{cid}")

    def test_cli_single_field_conversation_id(self) -> None:
        cid = "33333333-3333-3333-3333-333333333333"
        stdout = io.StringIO()
        with (
            patch("sys.stdout", stdout),
            patch.dict(
                os.environ,
                {antigravity_session.ANTIGRAVITY_CONVERSATION_ID_ENV: cid},
                clear=True,
            ),
        ):
            code = antigravity_session.run_current_antigravity_conversation_id_cli(
                ["--field", "conversation-id"]
            )

        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue().strip(), cid)

    def test_cli_emits_warning_on_latest_fallback(self) -> None:
        cid = "44444444-4444-4444-4444-444444444444"
        with tempfile.TemporaryDirectory() as tmp:
            app_dir = Path(tmp)
            log_dir = app_dir / "brain" / cid / ".system_generated" / "logs"
            log_dir.mkdir(parents=True)
            (log_dir / "transcript.jsonl").write_text("{}\n", encoding="utf-8")

            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                patch("sys.stdout", stdout),
                patch("sys.stderr", stderr),
                patch.dict(os.environ, {}, clear=True),
            ):
                code = antigravity_session.run_current_antigravity_conversation_id_cli(
                    ["--latest", "--app-data-dir", str(app_dir)]
                )

            self.assertEqual(code, 0)
            self.assertIn(
                "warning: resolved Antigravity conversation ID", stderr.getvalue()
            )
            self.assertIn(cid, stdout.getvalue())

    def test_cli_fails_with_exit_code_2_when_unresolvable(self) -> None:
        stderr = io.StringIO()
        with (
            patch("sys.stderr", stderr),
            patch.dict(os.environ, {}, clear=True),
        ):
            code = antigravity_session.run_current_antigravity_conversation_id_cli([])

        self.assertEqual(code, 2)
        self.assertIn("error:", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
