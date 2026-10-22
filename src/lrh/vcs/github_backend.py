"""GitHub implementation of the VCS backend, built on the ``gh`` CLI."""

from __future__ import annotations

import pathlib
import re

from lrh.integrations.github import gh_client
from lrh.vcs import backend

_PULL_REQUEST_URL = re.compile(r"https://[^/\s]+/[^/\s]+/[^/\s]+/pull/[0-9]+/?")


def _require_pull_request_url(pr: str) -> None:
    # gh resolves a bare number or branch against the current directory's
    # repository, which could differ between the read and the merge.
    if not _PULL_REQUEST_URL.fullmatch(pr):
        raise backend.MergeRefusedError(
            "the github backend needs a pull request URL "
            "(https://<host>/<owner>/<repo>/pull/<number>)"
        )


class GitHubBackend:
    """Talks to GitHub through ``gh``; the pull request is always a URL."""

    name = "github"

    def __init__(self, cwd: str | pathlib.Path | None = None) -> None:
        self._cwd = cwd

    def get_pull_request(self, pr: str) -> backend.PullRequestInfo:
        _require_pull_request_url(pr)
        try:
            payload = gh_client.run_gh_json(
                ["pr", "view", pr, "--json", "state,headRefOid,mergeCommit"],
                cwd=self._cwd,
            )
        except RuntimeError as err:
            raise backend.VcsError(str(err)) from err
        if not isinstance(payload, dict):
            raise backend.VcsError("gh returned an unexpected payload for pr view")
        state = payload.get("state")
        head_sha = payload.get("headRefOid")
        if not isinstance(state, str) or not isinstance(head_sha, str):
            raise backend.VcsError("gh pr view did not report state and head commit")
        merge_commit = payload.get("mergeCommit")
        oid = merge_commit.get("oid") if isinstance(merge_commit, dict) else None
        return backend.PullRequestInfo(
            url=pr,
            state=state.upper(),
            head_sha=head_sha,
            merge_commit=oid if isinstance(oid, str) and oid else None,
        )

    def merge_pull_request(self, pr: str, *, mode: str, match_head_commit: str) -> None:
        _require_pull_request_url(pr)
        try:
            gh_client.run_gh(
                [
                    "pr",
                    "merge",
                    pr,
                    f"--{mode}",
                    "--match-head-commit",
                    match_head_commit,
                ],
                cwd=self._cwd,
            )
        except RuntimeError as err:
            raise backend.VcsError(str(err)) from err
