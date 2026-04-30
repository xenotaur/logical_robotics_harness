import contextlib
import io
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

    def test_unresolved_command_uses_unresolved_format_mode(self) -> None:
        out = io.StringIO()
        with (
            mock.patch(
                "lrh.cli.github.pull_reviews.get_pull_review_threads",
                return_value={"data": {}},
            ),
            mock.patch(
                "lrh.cli.github.formatters.format_threads", return_value="unresolved=2"
            ) as fmt,
            contextlib.redirect_stdout(out),
        ):
            code = github.run_github_cli(["unresolved", "a/b", "3"], prog="lrh github")
        self.assertEqual(code, 0)
        fmt.assert_called_once_with({"data": {}}, only_unresolved=True)
        self.assertIn("unresolved=2", out.getvalue())


if __name__ == "__main__":
    unittest.main()
