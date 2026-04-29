"""Pull request reference parsing for GitHub integrations."""

from __future__ import annotations

import re
from dataclasses import dataclass

_PR_URL_RE = re.compile(
    r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)",
)


@dataclass(frozen=True)
class PullRequestRef:
    owner: str
    repo: str
    number: int


def parse_pull_request_ref(repo: str, number: int) -> PullRequestRef:
    """Parse owner/repo and PR number values."""
    parts = repo.split("/")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(f"Invalid repository reference: {repo}")
    return PullRequestRef(owner=parts[0], repo=parts[1], number=number)


def parse_pull_request_url(url: str) -> PullRequestRef:
    """Parse a GitHub pull request URL into a typed reference."""
    match = _PR_URL_RE.match(url)
    if match is None:
        raise ValueError(f"Invalid pull request URL: {url}")
    return PullRequestRef(
        owner=match.group("owner"),
        repo=match.group("repo"),
        number=int(match.group("number")),
    )
