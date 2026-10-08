import unittest
from unittest import mock

from lrh.vcs import backend, github_backend, registry

PR = "https://github.com/o/r/pull/7"
SHA = "a" * 40
OTHER_SHA = "b" * 40
MERGE_COMMIT = "c" * 40


def _info(
    state: str = "OPEN", head: str = SHA, merge_commit: str | None = None
) -> backend.PullRequestInfo:
    return backend.PullRequestInfo(
        url=PR, state=state, head_sha=head, merge_commit=merge_commit
    )


class FakeBackend:
    name = "fake"

    def __init__(
        self,
        responses: list[backend.PullRequestInfo | Exception],
        merge_error: Exception | None = None,
    ) -> None:
        self._responses = list(responses)
        self._merge_error = merge_error
        self.merge_calls: list[tuple[str, str, str]] = []
        self.get_calls = 0

    def get_pull_request(self, pr: str) -> backend.PullRequestInfo:
        self.get_calls += 1
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def merge_pull_request(self, pr: str, *, mode: str, match_head_commit: str) -> None:
        self.merge_calls.append((pr, mode, match_head_commit))
        if self._merge_error is not None:
            raise self._merge_error


class MergePullRequestLockedTest(unittest.TestCase):
    def test_merges_open_pr_at_verified_head(self) -> None:
        fake = FakeBackend([_info(), _info("MERGED", merge_commit=MERGE_COMMIT)])
        outcome = backend.merge_pull_request_locked(
            fake, PR, mode="merge", match_head_commit=SHA
        )
        self.assertEqual("merged", outcome.status)
        self.assertEqual(MERGE_COMMIT, outcome.merge_commit)
        self.assertEqual([(PR, "merge", SHA)], fake.merge_calls)

    def test_reports_queued_when_state_is_not_merged_after_merge(self) -> None:
        fake = FakeBackend([_info(), _info("OPEN")])
        outcome = backend.merge_pull_request_locked(
            fake, PR, mode="squash", match_head_commit=SHA
        )
        self.assertEqual("queued", outcome.status)
        self.assertEqual("OPEN", outcome.state)
        self.assertIsNone(outcome.merge_commit)
        self.assertEqual(1, len(fake.merge_calls))

    def test_merged_without_reported_commit_is_still_merged(self) -> None:
        fake = FakeBackend([_info(), _info("MERGED")])
        outcome = backend.merge_pull_request_locked(
            fake, PR, mode="rebase", match_head_commit=SHA
        )
        self.assertEqual("merged", outcome.status)
        self.assertIsNone(outcome.merge_commit)

    def test_refuses_pr_that_is_not_open_without_merging(self) -> None:
        for state in ("MERGED", "CLOSED"):
            with self.subTest(state=state):
                fake = FakeBackend([_info(state)])
                with self.assertRaises(backend.MergeRefusedError) as ctx:
                    backend.merge_pull_request_locked(
                        fake, PR, mode="merge", match_head_commit=SHA
                    )
                self.assertIn(state, str(ctx.exception))
                self.assertEqual([], fake.merge_calls)

    def test_refuses_when_head_moved_past_verified_commit(self) -> None:
        fake = FakeBackend([_info(head=OTHER_SHA)])
        with self.assertRaises(backend.MergeRefusedError) as ctx:
            backend.merge_pull_request_locked(
                fake, PR, mode="merge", match_head_commit=SHA
            )
        self.assertIn(OTHER_SHA, str(ctx.exception))
        self.assertIn(SHA, str(ctx.exception))
        self.assertEqual([], fake.merge_calls)

    def test_rejects_malformed_sha_before_any_backend_call(self) -> None:
        for bad in ("abc123", "A" * 40, "g" * 40, SHA + "0", ""):
            with self.subTest(sha=bad):
                fake = FakeBackend([])
                with self.assertRaises(backend.MergeRefusedError):
                    backend.merge_pull_request_locked(
                        fake, PR, mode="merge", match_head_commit=bad
                    )
                self.assertEqual(0, fake.get_calls)
                self.assertEqual([], fake.merge_calls)

    def test_rejects_unknown_mode_before_any_backend_call(self) -> None:
        fake = FakeBackend([])
        with self.assertRaises(backend.MergeRefusedError):
            backend.merge_pull_request_locked(
                fake, PR, mode="--delete-branch", match_head_commit=SHA
            )
        self.assertEqual(0, fake.get_calls)

    def test_rejects_empty_or_option_shaped_pr_reference(self) -> None:
        for bad in ("", "--delete-branch"):
            with self.subTest(pr=bad):
                fake = FakeBackend([])
                with self.assertRaises(backend.MergeRefusedError):
                    backend.merge_pull_request_locked(
                        fake, bad, mode="merge", match_head_commit=SHA
                    )
                self.assertEqual(0, fake.get_calls)

    def test_failed_merge_call_reports_state_and_is_not_retried(self) -> None:
        fake = FakeBackend(
            [_info(), _info("OPEN")], merge_error=backend.VcsError("boom")
        )
        with self.assertRaises(backend.VcsError) as ctx:
            backend.merge_pull_request_locked(
                fake, PR, mode="merge", match_head_commit=SHA
            )
        self.assertNotIsInstance(ctx.exception, backend.MergeRefusedError)
        self.assertEqual("boom; the pull request is now OPEN", str(ctx.exception))
        self.assertEqual(1, len(fake.merge_calls))
        self.assertEqual(2, fake.get_calls)

    def test_failed_merge_call_says_so_when_the_pr_merged_anyway(self) -> None:
        fake = FakeBackend(
            [_info(), _info("MERGED", merge_commit=MERGE_COMMIT)],
            merge_error=backend.VcsError("connection reset"),
        )
        with self.assertRaises(backend.VcsError) as ctx:
            backend.merge_pull_request_locked(
                fake, PR, mode="merge", match_head_commit=SHA
            )
        self.assertIn("connection reset", str(ctx.exception))
        self.assertIn("now MERGED", str(ctx.exception))
        self.assertEqual(1, len(fake.merge_calls))

    def test_failed_merge_call_with_unreadable_state_says_to_check(self) -> None:
        fake = FakeBackend(
            [_info(), backend.VcsError("net down")],
            merge_error=backend.VcsError("boom"),
        )
        with self.assertRaises(backend.VcsError) as ctx:
            backend.merge_pull_request_locked(
                fake, PR, mode="merge", match_head_commit=SHA
            )
        self.assertIn("boom", str(ctx.exception))
        self.assertIn("could not be read afterwards", str(ctx.exception))
        self.assertIn("net down", str(ctx.exception))
        self.assertEqual(1, len(fake.merge_calls))

    def test_closed_pr_after_an_issued_merge_is_a_verification_error(self) -> None:
        fake = FakeBackend([_info(), _info("CLOSED")])
        with self.assertRaises(backend.MergeVerificationError) as ctx:
            backend.merge_pull_request_locked(
                fake, PR, mode="merge", match_head_commit=SHA
            )
        self.assertIn("CLOSED", str(ctx.exception))
        self.assertIn("not MERGED or OPEN", str(ctx.exception))

    def test_verification_failure_says_the_merge_was_issued(self) -> None:
        fake = FakeBackend([_info(), backend.VcsError("net down")])
        with self.assertRaises(backend.MergeVerificationError) as ctx:
            backend.merge_pull_request_locked(
                fake, PR, mode="merge", match_head_commit=SHA
            )
        self.assertIn("merge command was issued", str(ctx.exception))
        self.assertIn("net down", str(ctx.exception))
        self.assertEqual(1, len(fake.merge_calls))


def _decode_error() -> UnicodeDecodeError:
    return UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")


class UnexpectedBackendErrorTest(unittest.TestCase):
    """A pluggable backend may raise any exception type; none may escape."""

    def test_unexpected_error_from_the_merge_call_reports_type_and_state(self) -> None:
        fake = FakeBackend([_info(), _info("OPEN")], merge_error=_decode_error())
        with self.assertRaises(backend.VcsError) as ctx:
            backend.merge_pull_request_locked(
                fake, PR, mode="merge", match_head_commit=SHA
            )
        self.assertIn("UnicodeDecodeError", str(ctx.exception))
        self.assertIn("now OPEN", str(ctx.exception))
        self.assertEqual(1, len(fake.merge_calls))

    def test_unexpected_error_on_read_back_is_a_verification_error(self) -> None:
        fake = FakeBackend([_info(), _decode_error()])
        with self.assertRaises(backend.MergeVerificationError) as ctx:
            backend.merge_pull_request_locked(
                fake, PR, mode="merge", match_head_commit=SHA
            )
        self.assertIn("merge command was issued", str(ctx.exception))
        self.assertIn("UnicodeDecodeError", str(ctx.exception))
        self.assertEqual(1, len(fake.merge_calls))

    def test_unexpected_error_before_the_merge_says_no_merge_was_issued(self) -> None:
        fake = FakeBackend([RuntimeError("boom")])
        with self.assertRaises(backend.VcsError) as ctx:
            backend.merge_pull_request_locked(
                fake, PR, mode="merge", match_head_commit=SHA
            )
        self.assertNotIsInstance(ctx.exception, backend.MergeRefusedError)
        self.assertIn("no merge was issued", str(ctx.exception))
        self.assertIn("RuntimeError: boom", str(ctx.exception))
        self.assertEqual([], fake.merge_calls)

    def test_unexpected_error_reading_state_after_a_failed_merge_call(self) -> None:
        fake = FakeBackend(
            [_info(), ValueError("odd")], merge_error=backend.VcsError("boom")
        )
        with self.assertRaises(backend.VcsError) as ctx:
            backend.merge_pull_request_locked(
                fake, PR, mode="merge", match_head_commit=SHA
            )
        self.assertIn("boom", str(ctx.exception))
        self.assertIn("could not be read afterwards", str(ctx.exception))
        self.assertIn("ValueError: odd", str(ctx.exception))

    def test_backend_errors_before_the_merge_keep_their_own_type(self) -> None:
        fake = FakeBackend([backend.MergeRefusedError("not a URL")])
        with self.assertRaises(backend.MergeRefusedError):
            backend.merge_pull_request_locked(
                fake, PR, mode="merge", match_head_commit=SHA
            )
        self.assertEqual([], fake.merge_calls)


class GitHubBackendTest(unittest.TestCase):
    def test_get_pull_request_parses_gh_payload(self) -> None:
        payload = {
            "state": "merged",
            "headRefOid": SHA,
            "mergeCommit": {"oid": MERGE_COMMIT},
        }
        with mock.patch(
            "lrh.vcs.github_backend.gh_client.run_gh_json", return_value=payload
        ) as run:
            info = github_backend.GitHubBackend().get_pull_request(PR)
        self.assertEqual("MERGED", info.state)
        self.assertEqual(SHA, info.head_sha)
        self.assertEqual(MERGE_COMMIT, info.merge_commit)
        run.assert_called_once_with(
            ["pr", "view", PR, "--json", "state,headRefOid,mergeCommit"], cwd=None
        )

    def test_get_pull_request_treats_null_merge_commit_as_none(self) -> None:
        payload = {"state": "OPEN", "headRefOid": SHA, "mergeCommit": None}
        with mock.patch(
            "lrh.vcs.github_backend.gh_client.run_gh_json", return_value=payload
        ):
            info = github_backend.GitHubBackend().get_pull_request(PR)
        self.assertIsNone(info.merge_commit)

    def test_get_pull_request_rejects_unexpected_payloads(self) -> None:
        for payload in ([], {"state": "OPEN"}, {"headRefOid": SHA}):
            with self.subTest(payload=payload):
                with mock.patch(
                    "lrh.vcs.github_backend.gh_client.run_gh_json",
                    return_value=payload,
                ):
                    with self.assertRaises(backend.VcsError):
                        github_backend.GitHubBackend().get_pull_request(PR)

    def test_get_pull_request_wraps_gh_errors_keeping_the_message(self) -> None:
        with mock.patch(
            "lrh.vcs.github_backend.gh_client.run_gh_json",
            side_effect=RuntimeError("gh CLI not found"),
        ):
            with self.assertRaises(backend.VcsError) as ctx:
                github_backend.GitHubBackend().get_pull_request(PR)
        self.assertEqual("gh CLI not found", str(ctx.exception))

    def test_merge_pull_request_builds_the_exact_locked_command(self) -> None:
        with mock.patch("lrh.vcs.github_backend.gh_client.run_gh") as run:
            github_backend.GitHubBackend().merge_pull_request(
                PR, mode="squash", match_head_commit=SHA
            )
        run.assert_called_once_with(
            ["pr", "merge", PR, "--squash", "--match-head-commit", SHA], cwd=None
        )

    def test_merge_pull_request_wraps_gh_errors_keeping_the_message(self) -> None:
        with mock.patch(
            "lrh.vcs.github_backend.gh_client.run_gh",
            side_effect=RuntimeError("head branch was modified"),
        ):
            with self.assertRaises(backend.VcsError) as ctx:
                github_backend.GitHubBackend().merge_pull_request(
                    PR, mode="merge", match_head_commit=SHA
                )
        self.assertEqual("head branch was modified", str(ctx.exception))


class GitHubBackendUrlTest(unittest.TestCase):
    def test_non_url_references_are_refused_before_any_gh_call(self) -> None:
        for ref in (
            "7",
            "feature-branch",
            "owner/repo#7",
            "http://github.com/o/r/pull/7",
        ):
            with self.subTest(ref=ref):
                with (
                    mock.patch("lrh.vcs.github_backend.gh_client.run_gh") as run,
                    mock.patch(
                        "lrh.vcs.github_backend.gh_client.run_gh_json"
                    ) as run_json,
                ):
                    gh = github_backend.GitHubBackend()
                    with self.assertRaises(backend.MergeRefusedError):
                        gh.get_pull_request(ref)
                    with self.assertRaises(backend.MergeRefusedError):
                        gh.merge_pull_request(ref, mode="merge", match_head_commit=SHA)
                run.assert_not_called()
                run_json.assert_not_called()

    def test_pull_request_urls_on_any_host_are_accepted(self) -> None:
        payload = {"state": "OPEN", "headRefOid": SHA, "mergeCommit": None}
        for url in (PR, "https://github.example.com/org/repo/pull/12/"):
            with self.subTest(url=url):
                with mock.patch(
                    "lrh.vcs.github_backend.gh_client.run_gh_json",
                    return_value=payload,
                ):
                    info = github_backend.GitHubBackend().get_pull_request(url)
                self.assertEqual(url, info.url)


class RegistryTest(unittest.TestCase):
    def test_lists_registered_backends(self) -> None:
        self.assertEqual(("github",), registry.backend_names())
        self.assertIn(registry.DEFAULT_BACKEND, registry.backend_names())

    def test_creates_the_github_backend(self) -> None:
        self.assertIsInstance(
            registry.create_backend("github"), github_backend.GitHubBackend
        )

    def test_unknown_backend_names_the_available_ones(self) -> None:
        with self.assertRaises(backend.VcsError) as ctx:
            registry.create_backend("mercurial")
        self.assertIn("mercurial", str(ctx.exception))
        self.assertIn("available: github", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
