"""GitHub PR review/comment data collection."""

from __future__ import annotations

from lrh.integrations.github import gh_client, pr_ref


def get_pull_review_threads(ref: pr_ref.PullRequestRef) -> object:
    query = (
        "query($owner: String!, $repo: String!, $number: Int!) {"
        " repository(owner: $owner, name: $repo) {"
        " pullRequest(number: $number) {"
        " reviewThreads(first: 100) {"
        " nodes { id isResolved isOutdated comments(first: 100) { nodes { id body author { login } url } } }"
        " } } } }"
    )
    return gh_client.run_gh_json([
        "api",
        "graphql",
        "-f",
        f"query={query}",
        "-F",
        f"owner={ref.owner}",
        "-F",
        f"repo={ref.repo}",
        "-F",
        f"number={ref.number}",
    ])


def get_pull_comments(ref: pr_ref.PullRequestRef) -> dict[str, object]:
    return {
        "review_comments": gh_client.run_gh_json(
            ["api", f"repos/{ref.owner}/{ref.repo}/pulls/{ref.number}/comments"]
        ),
        "issue_comments": gh_client.run_gh_json(
            ["api", f"repos/{ref.owner}/{ref.repo}/issues/{ref.number}/comments"]
        ),
        "review_threads": get_pull_review_threads(ref),
    }
