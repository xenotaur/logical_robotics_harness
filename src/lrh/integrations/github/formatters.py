"""Output formatters for GitHub integration commands."""

from __future__ import annotations


def format_comments(data: dict[str, object]) -> str:
    review_comments = data.get("review_comments")
    issue_comments = data.get("issue_comments")
    review_count = len(review_comments) if isinstance(review_comments, list) else 0
    issue_count = len(issue_comments) if isinstance(issue_comments, list) else 0
    return f"review_comments={review_count}\nissue_comments={issue_count}"


def format_threads(data: object, only_unresolved: bool = False) -> str:
    threads = (
        data.get("data", {})
        .get("repository", {})
        .get("pullRequest", {})
        .get("reviewThreads", {})
        .get("nodes", [])
        if isinstance(data, dict)
        else []
    )
    unresolved = 0
    for thread in threads:
        if (
            isinstance(thread, dict)
            and not thread.get("isResolved", False)
            and not thread.get("isOutdated", False)
        ):
            unresolved += 1
    if only_unresolved:
        return f"unresolved={unresolved}"
    return f"threads={len(threads)}\nunresolved={unresolved}"
