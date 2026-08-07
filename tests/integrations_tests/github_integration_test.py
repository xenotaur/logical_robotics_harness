import json
import unittest
from unittest import mock

from lrh.integrations.github import formatters, gh_client, pr_ref, pull_reviews


class GithubIntegrationTest(unittest.TestCase):
    def test_parse_repo_ref(self) -> None:
        ref = pr_ref.parse_pull_request_ref("octo/repo", 7)
        self.assertEqual(ref.owner, "octo")
        self.assertEqual(ref.repo, "repo")
        self.assertEqual(ref.number, 7)

    def test_parse_pr_url(self) -> None:
        ref = pr_ref.parse_pull_request_url("https://github.com/octo/repo/pull/11")
        self.assertEqual(ref.owner, "octo")
        self.assertEqual(ref.repo, "repo")
        self.assertEqual(ref.number, 11)

    def test_get_pull_comments_uses_paginate(self) -> None:
        ref = pr_ref.PullRequestRef("o", "r", 1)
        with mock.patch(
            "lrh.integrations.github.pull_reviews.gh_client.run_gh_json",
            side_effect=[
                [{"id": "r"}],
                [{"id": "i"}],
                {
                    "data": {
                        "repository": {"pullRequest": {"reviewThreads": {"nodes": []}}}
                    }
                },
            ],
        ) as run_json:
            data = pull_reviews.get_pull_comments(ref)
        self.assertIn("review_comments", data)
        review_call = run_json.call_args_list[0].args[0]
        issue_call = run_json.call_args_list[1].args[0]
        self.assertIn("--paginate", review_call)
        self.assertIn("--slurp", review_call)
        self.assertIn("--paginate", issue_call)
        self.assertIn("--slurp", issue_call)

    def test_format_review_mode_and_state_filter(self) -> None:
        data = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": [
                                {
                                    "path": "x.py",
                                    "line": 2,
                                    "isResolved": False,
                                    "isOutdated": False,
                                    "comments": {
                                        "nodes": [
                                            {
                                                "body": "fix",
                                                "author": {"login": "a"},
                                                "url": "u",
                                            }
                                        ]
                                    },
                                },
                                {
                                    "isResolved": True,
                                    "isOutdated": False,
                                    "comments": {"nodes": []},
                                },
                            ]
                        }
                    }
                }
            }
        }
        out = formatters.format_threads_review(
            data,
            state="unresolved",
            show_pr=True,
            include_author=True,
            include_url=True,
            ref=pr_ref.PullRequestRef("o", "r", 1),
        )
        self.assertIn("PR: o/r#1", out)
        self.assertIn("x.py:L2", out)
        self.assertIn("author: a", out)

    def test_collect_thread_ids_returns_all_ids(self) -> None:
        data = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": [
                                {"id": "T1", "isResolved": False},
                                {"id": "T2", "isResolved": True},
                                {"isResolved": False},
                            ]
                        }
                    }
                }
            }
        }
        self.assertEqual(formatters.collect_thread_ids(data), {"T1", "T2"})

    def test_resolved_thread_ids_returns_only_resolved(self) -> None:
        data = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": [
                                {"id": "T1", "isResolved": False},
                                {"id": "T2", "isResolved": True},
                            ]
                        }
                    }
                }
            }
        }
        self.assertEqual(formatters.resolved_thread_ids(data), {"T2"})

    def test_format_review_extra_ids_includes_outdated_unresolved_thread(
        self,
    ) -> None:
        data = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": [
                                {
                                    "id": "T1",
                                    "path": "x.py",
                                    "line": 2,
                                    "isResolved": False,
                                    "isOutdated": True,
                                    "comments": {
                                        "nodes": [
                                            {
                                                "body": "still needs a fix",
                                                "author": {"login": "a"},
                                                "url": "u",
                                            }
                                        ]
                                    },
                                },
                            ]
                        }
                    }
                }
            }
        }
        out = formatters.format_threads_review(
            data,
            state="unresolved",
            show_pr=True,
            include_author=True,
            include_url=True,
            ref=pr_ref.PullRequestRef("o", "r", 1),
            extra_ids={"T1"},
        )
        self.assertIn("still needs a fix", out)

    def test_format_review_extra_ids_excludes_already_resolved_thread(
        self,
    ) -> None:
        data = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": [
                                {
                                    "id": "T1",
                                    "path": "x.py",
                                    "line": 2,
                                    "isResolved": True,
                                    "isOutdated": True,
                                    "comments": {
                                        "nodes": [
                                            {
                                                "body": "already resolved",
                                                "author": {"login": "a"},
                                                "url": "u",
                                            }
                                        ]
                                    },
                                },
                            ]
                        }
                    }
                }
            }
        }
        out = formatters.format_threads_review(
            data,
            state="unresolved",
            show_pr=True,
            include_author=True,
            include_url=True,
            ref=pr_ref.PullRequestRef("o", "r", 1),
            extra_ids={"T1"},
        )
        self.assertNotIn("already resolved", out)
        self.assertNotIn("x.py:L2", out)

    def test_matches_state_extra_ids_does_not_leak_into_other_states(self) -> None:
        # A thread named in extra_ids is genuinely unresolved and not
        # outdated -- extra_ids must not cause it to match "resolved" or
        # "outdated" queries it doesn't actually satisfy.
        thread = {"id": "T1", "isResolved": False, "isOutdated": False}
        self.assertFalse(
            formatters._matches_state(thread, "resolved", extra_ids={"T1"})
        )
        self.assertFalse(
            formatters._matches_state(thread, "outdated", extra_ids={"T1"})
        )
        # "all" already matches everything regardless of extra_ids, so this
        # just confirms extra_ids doesn't break that either.
        self.assertTrue(formatters._matches_state(thread, "all", extra_ids={"T1"}))
        # The actual intended effect: still widens the "unresolved" branch.
        self.assertTrue(
            formatters._matches_state(
                {"id": "T1", "isResolved": False, "isOutdated": True},
                "unresolved",
                extra_ids={"T1"},
            )
        )

    def test_format_raw_mode(self) -> None:
        data = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": [
                                {
                                    "isResolved": False,
                                    "isOutdated": False,
                                    "comments": {"nodes": []},
                                }
                            ]
                        }
                    }
                }
            }
        }
        out = formatters.format_threads_raw(
            data,
            state="unresolved",
            show_pr=False,
            ref=pr_ref.PullRequestRef("o", "r", 1),
        )
        parsed = json.loads(out)
        self.assertEqual(len(parsed["threads"]), 1)
        self.assertNotIn("pull_request", parsed)

    def test_run_gh_json_raises_clean_errors(self) -> None:
        with mock.patch("subprocess.run", side_effect=FileNotFoundError()):
            with self.assertRaisesRegex(RuntimeError, "gh CLI not found"):
                gh_client.run_gh_json(["api"])


if __name__ == "__main__":
    unittest.main()
