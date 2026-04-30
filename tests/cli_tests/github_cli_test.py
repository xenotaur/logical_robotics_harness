import contextlib
import io
import json
import unittest
from unittest import mock

from lrh.cli import github


class GithubCliTest(unittest.TestCase):
    def test_comments_command(self) -> None:
        out = io.StringIO()
        with (
            mock.patch(
                "lrh.cli.github.pull_reviews.get_pull_comments",
                return_value={"review_comments": [], "issue_comments": []},
            ),
            contextlib.redirect_stdout(out),
        ):
            code = github.run_github_cli(["comments", "a/b", "3"], prog="lrh github")
        self.assertEqual(code, 0)
        self.assertIn("review_comments=0", out.getvalue())

    def test_unresolved_command_forces_unresolved_state(self) -> None:
        out = io.StringIO()
        with (
            mock.patch(
                "lrh.cli.github.pull_reviews.get_pull_review_threads",
                return_value={"data": {}},
            ),
            mock.patch(
                "lrh.cli.github.formatters.format_threads_review",
                return_value="ok",
            ) as fmt,
            contextlib.redirect_stdout(out),
        ):
            code = github.run_github_cli(
                ["unresolved", "a/b", "3", "--state", "all"], prog="lrh github"
            )
        self.assertEqual(code, 0)
        self.assertEqual("ok\n", out.getvalue())
        self.assertEqual(fmt.call_args.kwargs["state"], "unresolved")

    def test_threads_parses_url_target(self) -> None:
        out = io.StringIO()
        with (
            mock.patch(
                "lrh.cli.github.pull_reviews.get_pull_review_threads", return_value={}
            ),
            mock.patch(
                "lrh.cli.github.formatters.format_threads_review", return_value="ok"
            ),
            contextlib.redirect_stdout(out),
        ):
            code = github.run_github_cli(
                ["threads", "https://github.com/o/r/pull/5"], prog="lrh github"
            )
        self.assertEqual(0, code)

    def test_threads_raw_mode(self) -> None:
        out = io.StringIO()
        with (
            mock.patch(
                "lrh.cli.github.pull_reviews.get_pull_review_threads", return_value={}
            ),
            mock.patch(
                "lrh.cli.github.formatters.format_threads_raw", return_value='{"a":1}'
            ),
            contextlib.redirect_stdout(out),
        ):
            github.run_github_cli(
                ["threads", "a/b", "3", "--mode", "raw"], prog="lrh github"
            )
        self.assertEqual('{"a":1}\n', out.getvalue())

    def test_comments_raw_mode_json_output(self) -> None:
        out = io.StringIO()
        with (
            mock.patch(
                "lrh.cli.github.pull_reviews.get_pull_comments",
                return_value={"issue_comments": [], "review_comments": []},
            ),
            contextlib.redirect_stdout(out),
        ):
            github.run_github_cli(
                ["comments", "a/b", "1", "--mode", "raw"], prog="lrh github"
            )
        parsed = json.loads(out.getvalue())
        self.assertEqual(parsed["issue_comments"], [])

    def test_missing_number_reports_cli_usage_error(self) -> None:
        out = io.StringIO()
        err = io.StringIO()
        with (
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
            with self.assertRaises(SystemExit) as exc:
                github.run_github_cli(["threads", "a/b"], prog="lrh github")
        self.assertEqual(exc.exception.code, 2)
        self.assertIn("number is required", err.getvalue())

    def test_threads_fetch_error_returns_nonzero(self) -> None:
        out = io.StringIO()
        err = io.StringIO()
        with (
            mock.patch(
                "lrh.cli.github.pull_reviews.get_pull_review_threads",
                side_effect=ValueError(
                    "error: pull request not found or inaccessible: a/b#3"
                ),
            ),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
            code = github.run_github_cli(["threads", "a/b", "3"], prog="lrh github")
        self.assertEqual(code, 2)
        self.assertEqual("", out.getvalue())
        self.assertIn("pull request not found or inaccessible", err.getvalue())


if __name__ == "__main__":
    unittest.main()
