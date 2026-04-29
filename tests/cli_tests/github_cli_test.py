import contextlib
import io
import unittest
from unittest import mock

from lrh.cli import github


class GithubCliTest(unittest.TestCase):
    def test_comments_command(self) -> None:
        out = io.StringIO()
        with (
            mock.patch("lrh.cli.github.pull_reviews.get_pull_comments", return_value={"review_comments": [], "issue_comments": []}),
            contextlib.redirect_stdout(out),
        ):
            code = github.run_github_cli(["comments", "a/b", "3"], prog="lrh github")
        self.assertEqual(code, 0)
        self.assertIn("review_comments=0", out.getvalue())


if __name__ == "__main__":
    unittest.main()
