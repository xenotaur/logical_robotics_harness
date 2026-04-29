import unittest
from unittest import mock

from lrh.integrations.github import formatters, gh_client, pr_ref, pull_reviews


class GithubIntegrationTest(unittest.TestCase):
    def test_parse_repo_ref(self) -> None:
        ref = pr_ref.parse_pull_request_ref("octo/repo", 7)
        self.assertEqual(ref.owner, "octo")
        self.assertEqual(ref.repo, "repo")
        self.assertEqual(ref.number, 7)

    def test_get_pull_comments_uses_paginate(self) -> None:
        ref = pr_ref.PullRequestRef("o", "r", 1)
        with mock.patch(
            "lrh.integrations.github.pull_reviews.gh_client.run_gh_json",
            side_effect=[[{"id": "r"}], [{"id": "i"}], {"data": {"repository": {"pullRequest": {"reviewThreads": {"nodes": []}}}}}],
        ) as run_json:
            data = pull_reviews.get_pull_comments(ref)
        self.assertIn("review_comments", data)
        review_call = run_json.call_args_list[0].args[0]
        issue_call = run_json.call_args_list[1].args[0]
        self.assertIn("--paginate", review_call)
        self.assertIn("--slurp", review_call)
        self.assertIn("--paginate", issue_call)
        self.assertIn("--slurp", issue_call)

    def test_format_threads_counts_unresolved_not_outdated(self) -> None:
        data = {"data": {"repository": {"pullRequest": {"reviewThreads": {"nodes": [
            {"isResolved": False, "isOutdated": False},
            {"isResolved": False, "isOutdated": True},
            {"isResolved": True, "isOutdated": False},
        ]}}}}}
        output = formatters.format_threads(data)
        self.assertIn("threads=3", output)
        self.assertIn("unresolved=1", output)

    def test_run_gh_json_raises_clean_errors(self) -> None:
        with mock.patch("subprocess.run", side_effect=FileNotFoundError()):
            with self.assertRaisesRegex(RuntimeError, "gh CLI not found"):
                gh_client.run_gh_json(["api"])


if __name__ == "__main__":
    unittest.main()
