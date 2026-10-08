import json
import unittest
from unittest import mock

from lrh.cli import main as cli_main
from lrh.cli import vcs
from lrh.vcs import backend
from tests import testing_support

PR = "https://github.com/o/r/pull/7"
SHA = "a" * 40
MERGE_COMMIT = "c" * 40


class FakeBackend:
    name = "fake"

    def __init__(
        self, states: list[str | Exception], merge_error: Exception | None = None
    ) -> None:
        self._states = list(states)
        self._merge_error = merge_error
        self.merge_calls: list[tuple[str, str, str]] = []

    def get_pull_request(self, pr: str) -> backend.PullRequestInfo:
        state = self._states.pop(0)
        if isinstance(state, Exception):
            raise state
        return backend.PullRequestInfo(
            url=pr,
            state=state,
            head_sha=SHA,
            merge_commit=MERGE_COMMIT if state == "MERGED" else None,
        )

    def merge_pull_request(self, pr: str, *, mode: str, match_head_commit: str) -> None:
        self.merge_calls.append((pr, mode, match_head_commit))
        if self._merge_error is not None:
            raise self._merge_error


def _run(
    argv: list[str], fake: FakeBackend
) -> tuple[int, testing_support.CapturedOutput]:
    with (
        mock.patch("lrh.cli.vcs.registry.create_backend", return_value=fake),
        testing_support.capture_output() as captured,
    ):
        code = vcs.run_vcs_cli(argv, prog="lrh vcs")
    return code, captured


class VcsMergeCliTest(unittest.TestCase):
    def test_merged_exits_zero_and_prints_the_merge_commit(self) -> None:
        fake = FakeBackend(["OPEN", "MERGED"])
        code, captured = _run(
            ["merge", PR, "--merge", "--match-head-commit", SHA], fake
        )
        self.assertEqual(0, code)
        self.assertEqual(f"merged: {MERGE_COMMIT}\n", captured.stdout.getvalue())
        self.assertEqual("", captured.stderr.getvalue())
        self.assertEqual([(PR, "merge", SHA)], fake.merge_calls)

    def test_mode_flag_selects_the_merge_method(self) -> None:
        fake = FakeBackend(["OPEN", "MERGED"])
        _run(["merge", PR, "--squash", "--match-head-commit", SHA], fake)
        self.assertEqual([(PR, "squash", SHA)], fake.merge_calls)

    def test_json_format_reports_status_fields(self) -> None:
        fake = FakeBackend(["OPEN", "MERGED"])
        code, captured = _run(
            ["merge", PR, "--merge", "--match-head-commit", SHA, "--format", "json"],
            fake,
        )
        self.assertEqual(0, code)
        self.assertEqual(
            {
                "status": "merged",
                "state": "MERGED",
                "merge_commit": MERGE_COMMIT,
                "backend": "github",
                "pr": PR,
            },
            json.loads(captured.stdout.getvalue()),
        )

    def test_queued_exits_one_and_says_to_recheck(self) -> None:
        fake = FakeBackend(["OPEN", "OPEN"])
        code, captured = _run(
            ["merge", PR, "--merge", "--match-head-commit", SHA], fake
        )
        self.assertEqual(1, code)
        self.assertIn("queued", captured.stdout.getvalue())
        self.assertIn("re-check", captured.stdout.getvalue())

    def test_refusal_exits_two_on_stderr_and_does_not_merge(self) -> None:
        fake = FakeBackend(["CLOSED"])
        code, captured = _run(
            ["merge", PR, "--merge", "--match-head-commit", SHA], fake
        )
        self.assertEqual(2, code)
        self.assertTrue(captured.stderr.getvalue().startswith("refused:"))
        self.assertEqual("", captured.stdout.getvalue())
        self.assertEqual([], fake.merge_calls)

    def test_failed_merge_call_reports_the_pr_state_on_stderr(self) -> None:
        fake = FakeBackend(["OPEN", "OPEN"], merge_error=backend.VcsError("boom"))
        code, captured = _run(
            ["merge", PR, "--merge", "--match-head-commit", SHA], fake
        )
        self.assertEqual(2, code)
        self.assertEqual(
            "error: boom; the pull request is now OPEN\n", captured.stderr.getvalue()
        )
        self.assertEqual(1, len(fake.merge_calls))

    def test_unreadable_final_state_exits_two_and_says_the_merge_was_issued(
        self,
    ) -> None:
        fake = FakeBackend(["OPEN", backend.VcsError("net down")])
        code, captured = _run(
            ["merge", PR, "--merge", "--match-head-commit", SHA], fake
        )
        self.assertEqual(2, code)
        self.assertIn("merge command was issued", captured.stderr.getvalue())
        self.assertEqual("", captured.stdout.getvalue())
        self.assertEqual(1, len(fake.merge_calls))

    def test_unexpected_exception_after_the_merge_exits_two_not_one(self) -> None:
        # An unhandled exception would exit 1, the code documented as "queued".
        fake = FakeBackend(
            ["OPEN", UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")]
        )
        code, captured = _run(
            ["merge", PR, "--merge", "--match-head-commit", SHA], fake
        )
        self.assertEqual(2, code)
        self.assertIn("merge command was issued", captured.stderr.getvalue())
        self.assertIn("UnicodeDecodeError", captured.stderr.getvalue())
        self.assertEqual("", captured.stdout.getvalue())
        self.assertEqual(1, len(fake.merge_calls))

    def test_backend_flag_selects_the_backend_by_name(self) -> None:
        fake = FakeBackend(["OPEN", "MERGED"])
        with (
            mock.patch(
                "lrh.cli.vcs.registry.create_backend", return_value=fake
            ) as create,
            testing_support.suppress_output(),
        ):
            vcs.run_vcs_cli(
                ["merge", PR, "--merge", "--match-head-commit", SHA]
                + ["--backend", "github"],
                prog="lrh vcs",
            )
        create.assert_called_once_with("github")

    def test_unknown_backend_and_missing_flags_are_usage_errors(self) -> None:
        cases = {
            "unknown backend": ["merge", PR, "--merge", "--match-head-commit", SHA]
            + ["--backend", "mercurial"],
            "no merge mode": ["merge", PR, "--match-head-commit", SHA],
            "no head commit": ["merge", PR, "--merge"],
            "two merge modes": ["merge", PR, "--merge", "--squash"]
            + ["--match-head-commit", SHA],
        }
        for label, argv in cases.items():
            with self.subTest(label):
                with testing_support.suppress_output():
                    with self.assertRaises(SystemExit) as ctx:
                        vcs.run_vcs_cli(argv, prog="lrh vcs")
                self.assertEqual(2, ctx.exception.code)

    def test_top_level_lrh_dispatches_vcs_merge(self) -> None:
        fake = FakeBackend(["OPEN", "MERGED"])
        argv = ["lrh", "vcs", "merge", PR, "--merge", "--match-head-commit", SHA]
        with (
            mock.patch("sys.argv", argv),
            mock.patch("lrh.cli.vcs.registry.create_backend", return_value=fake),
            testing_support.capture_output() as captured,
        ):
            with self.assertRaises(SystemExit) as ctx:
                cli_main.main()
        self.assertEqual(0, ctx.exception.code)
        self.assertEqual(f"merged: {MERGE_COMMIT}\n", captured.stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
