import unittest
from unittest import mock

from lrh.integrations.github import formatters, pr_ref, pull_reviews


class GithubIntegrationTest(unittest.TestCase):
    def test_parse_repo_ref(self) -> None:
        ref = pr_ref.parse_pull_request_ref("octo/repo", 7)
        self.assertEqual(ref.owner, "octo")
        self.assertEqual(ref.repo, "repo")
        self.assertEqual(ref.number, 7)

    def test_get_pull_comments_collects_all_types(self) -> None:
        ref = pr_ref.PullRequestRef("o", "r", 1)
        with mock.patch(
            "lrh.integrations.github.pull_reviews.gh_client.run_gh_json",
            side_effect=[[{"id": "r"}], [{"id": "i"}], {"data": {}}],
        ):
            data = pull_reviews.get_pull_comments(ref)
        self.assertIn("review_comments", data)
        self.assertIn("issue_comments", data)
        self.assertIn("review_threads", data)

    def test_format_threads_counts_unresolved(self) -> None:
        data = {"data": {"repository": {"pullRequest": {"reviewThreads": {"nodes": [
            {"isResolved": False}, {"isResolved": True}
        ]}}}}}
        output = formatters.format_threads(data)
        self.assertIn("threads=2", output)
        self.assertIn("unresolved=1", output)


if __name__ == "__main__":
    unittest.main()
