import unittest

from lrh.conversations import codex_session


class TestCodexSessionIdentity(unittest.TestCase):
    def test_explicit_thread_id_wins_and_is_trimmed(self) -> None:
        identity = codex_session.resolve_codex_session_identity(
            " thread-explicit ",
            environ={"CODEX_THREAD_ID": "thread-env"},
        )

        self.assertEqual(identity.thread_id, "thread-explicit")
        self.assertEqual(
            identity.session_transcript,
            "codex-app:thread-explicit",
        )

    def test_environment_thread_id_is_used_when_explicit_id_missing(self) -> None:
        identity = codex_session.resolve_codex_session_identity(
            environ={"CODEX_THREAD_ID": " thread-env "}
        )

        self.assertEqual(identity.thread_id, "thread-env")
        self.assertEqual(identity.session_transcript, "codex-app:thread-env")

    def test_missing_thread_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            codex_session.CodexSessionIdentityError,
            "--thread-id or CODEX_THREAD_ID is required",
        ):
            codex_session.resolve_codex_session_identity(environ={})

    def test_whitespace_only_thread_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            codex_session.CodexSessionIdentityError,
            "--thread-id or CODEX_THREAD_ID is required",
        ):
            codex_session.resolve_codex_session_identity(
                environ={"CODEX_THREAD_ID": " \t\n"}
            )


if __name__ == "__main__":
    unittest.main()
