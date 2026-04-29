import importlib.machinery
import importlib.util
import pathlib
import subprocess
import unittest
from unittest import mock


def load_github_adapter() -> object:
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    script_path = repo_root / "scripts" / "adapters" / "github"
    loader = importlib.machinery.SourceFileLoader("github_adapter", str(script_path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise RuntimeError("Could not load github adapter script.")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class GithubAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = load_github_adapter()

    def test_run_gh_json_raises_on_graphql_errors(self) -> None:
        result = subprocess.CompletedProcess(
            args=["gh"],
            returncode=0,
            stdout='{"data": null, "errors": [{"message": "bad query"}]}',
            stderr="",
        )
        with mock.patch.object(self.adapter.subprocess, "run", return_value=result):
            with self.assertRaisesRegex(RuntimeError, "bad query"):
                self.adapter.run_gh_json(["graphql"])

    def test_get_review_threads_paginates_threads_and_comments(self) -> None:
        first_page = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "pageInfo": {"hasNextPage": True, "endCursor": "T1"},
                            "nodes": [
                                {
                                    "id": "thread-1",
                                    "isResolved": False,
                                    "isOutdated": False,
                                    "comments": {
                                        "pageInfo": {
                                            "hasNextPage": True,
                                            "endCursor": "C1",
                                        },
                                        "nodes": [{"id": "comment-1"}],
                                    },
                                }
                            ],
                        }
                    }
                }
            }
        }
        second_page = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                            "nodes": [
                                {
                                    "id": "thread-2",
                                    "isResolved": True,
                                    "isOutdated": False,
                                    "comments": {
                                        "pageInfo": {
                                            "hasNextPage": False,
                                            "endCursor": None,
                                        },
                                        "nodes": [{"id": "comment-2"}],
                                    },
                                }
                            ],
                        }
                    }
                }
            }
        }
        extra_comments = {
            "data": {
                "node": {
                    "comments": {
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                        "nodes": [{"id": "comment-1b"}],
                    }
                }
            }
        }

        with (
            mock.patch.object(
                self.adapter,
                "get_review_threads_page",
                side_effect=[first_page, second_page],
            ) as get_threads_page,
            mock.patch.object(
                self.adapter,
                "get_review_thread_comments",
                return_value=extra_comments,
            ) as get_comments,
        ):
            threads = self.adapter.get_review_threads("owner", "repo", 12)

        nodes = self.adapter.thread_nodes(threads)
        self.assertEqual([node["id"] for node in nodes], ["thread-1", "thread-2"])
        self.assertEqual(
            [comment["id"] for comment in self.adapter.thread_comments(nodes[0])],
            ["comment-1", "comment-1b"],
        )
        get_threads_page.assert_has_calls(
            [
                mock.call("owner", "repo", 12, None),
                mock.call("owner", "repo", 12, "T1"),
            ]
        )
        get_comments.assert_called_once_with("thread-1", "C1")

    def test_comments_review_filters_by_thread_state(self) -> None:
        data = {
            "review_comments": [
                {"node_id": "review-a", "path": "a.py", "body": "keep"},
                {"node_id": "review-b", "path": "b.py", "body": "drop"},
            ],
            "issue_comments": [{"body": "top-level"}],
            "review_threads": {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "reviewThreads": {
                                "nodes": [
                                    {
                                        "isResolved": False,
                                        "isOutdated": False,
                                        "comments": {"nodes": [{"id": "review-a"}]},
                                    },
                                    {
                                        "isResolved": True,
                                        "isOutdated": False,
                                        "comments": {"nodes": [{"id": "review-b"}]},
                                    },
                                ]
                            }
                        }
                    }
                }
            },
        }

        output = self.adapter.format_comments_review(
            data,
            "unresolved",
            include_author=False,
            include_url=False,
        )

        self.assertIn("keep", output)
        self.assertIn("top-level", output)
        self.assertNotIn("drop", output)

    def test_submitted_normalizes_to_reviews_alias(self) -> None:
        self.assertEqual(
            self.adapter.normalize_command(["pull", "submitted", "repo/name", "3"]),
            ["pull", "reviews", "repo/name", "3"],
        )
        self.assertEqual(
            self.adapter.normalize_command(["submitted", "repo/name", "3"]),
            ["pull", "reviews", "repo/name", "3"],
        )


if __name__ == "__main__":
    unittest.main()
