"""GitHub PR review/comment data collection."""

from __future__ import annotations

from lrh.integrations.github import gh_client, pr_ref


def _thread_page(ref: pr_ref.PullRequestRef, after: str | None) -> object:
    query = (
        "query($owner: String!, $repo: String!, $number: Int!, $after: String) {"
        " repository(owner: $owner, name: $repo) {"
        " pullRequest(number: $number) {"
        " reviewThreads(first: 100, after: $after) {"
        " pageInfo { hasNextPage endCursor }"
        " nodes { id isResolved isOutdated"
        " comments(first: 100) {"
        " pageInfo { hasNextPage endCursor }"
        " nodes { id body author { login } url }"
        " } }"
        " } } } }"
    )
    return gh_client.run_gh_json(
        [
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
            "-F",
            f"after={after or ''}",
        ]
    )


def _thread_comments_page(thread_id: str, after: str | None) -> object:
    query = (
        "query($threadId: ID!, $after: String) {"
        " node(id: $threadId) { ... on PullRequestReviewThread {"
        " comments(first: 100, after: $after) {"
        " pageInfo { hasNextPage endCursor }"
        " nodes { id body author { login } url }"
        " }"
        " } } }"
    )
    return gh_client.run_gh_json(
        [
            "api",
            "graphql",
            "-f",
            f"query={query}",
            "-F",
            f"threadId={thread_id}",
            "-F",
            f"after={after or ''}",
        ]
    )


def _extract_threads(page: object) -> dict[str, object] | None:
    if not isinstance(page, dict):
        return None
    data = page.get("data", {})
    if not isinstance(data, dict):
        return None
    repository = data.get("repository", {})
    if not isinstance(repository, dict):
        return None
    pull_request = repository.get("pullRequest")
    if pull_request is None:
        return None
    if not isinstance(pull_request, dict):
        return None
    review_threads = pull_request.get("reviewThreads", {})
    return review_threads if isinstance(review_threads, dict) else {}


def get_pull_review_threads(ref: pr_ref.PullRequestRef) -> object:
    nodes: list[dict[str, object]] = []
    cursor: str | None = None
    while True:
        page = _thread_page(ref, cursor)
        threads = _extract_threads(page)
        if threads is None:
            raise ValueError(
                "error: pull request not found or inaccessible: "
                f"{ref.owner}/{ref.repo}#{ref.number}"
            )
        page_nodes = threads.get("nodes")
        if not isinstance(page_nodes, list):
            page_nodes = []
        for thread in page_nodes:
            if not isinstance(thread, dict):
                continue
            comments = thread.get("comments")
            if not isinstance(comments, dict):
                comments = {}
            comment_nodes = comments.get("nodes")
            if not isinstance(comment_nodes, list):
                comment_nodes = []
            comment_page = comments.get("pageInfo")
            if not isinstance(comment_page, dict):
                comment_page = {}
            comment_cursor = (
                comment_page.get("endCursor")
                if comment_page.get("hasNextPage")
                else None
            )
            while comment_cursor:
                thread_id = str(thread.get("id", ""))
                extra = _thread_comments_page(thread_id, str(comment_cursor))
                extra_comments = (
                    extra.get("data", {}).get("node", {}).get("comments", {})
                    if isinstance(extra, dict)
                    else {}
                )
                if not isinstance(extra_comments, dict):
                    extra_comments = {}
                extra_nodes = extra_comments.get("nodes")
                if isinstance(extra_nodes, list):
                    comment_nodes.extend(
                        node for node in extra_nodes if isinstance(node, dict)
                    )
                extra_page = extra_comments.get("pageInfo")
                if not isinstance(extra_page, dict):
                    extra_page = {}
                comment_cursor = (
                    extra_page.get("endCursor")
                    if extra_page.get("hasNextPage")
                    else None
                )
            thread["comments"] = {
                "nodes": comment_nodes,
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            }
            nodes.append(thread)
        page_info = threads.get("pageInfo")
        if not isinstance(page_info, dict) or not page_info.get("hasNextPage"):
            break
        cursor = str(page_info.get("endCursor"))

    return {
        "data": {
            "repository": {
                "pullRequest": {
                    "reviewThreads": {
                        "nodes": nodes,
                    }
                }
            }
        }
    }


def get_pull_comments(ref: pr_ref.PullRequestRef) -> dict[str, object]:
    return {
        "review_comments": gh_client.run_gh_json(
            [
                "api",
                "--paginate",
                "--slurp",
                f"repos/{ref.owner}/{ref.repo}/pulls/{ref.number}/comments",
            ]
        ),
        "issue_comments": gh_client.run_gh_json(
            [
                "api",
                "--paginate",
                "--slurp",
                f"repos/{ref.owner}/{ref.repo}/issues/{ref.number}/comments",
            ]
        ),
        "review_threads": get_pull_review_threads(ref),
    }
