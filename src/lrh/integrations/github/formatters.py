"""Output formatters for GitHub integration commands."""

from __future__ import annotations

import json

from lrh.integrations.github import pr_ref


def format_comments(data: dict[str, object]) -> str:
    review_comments = data.get("review_comments")
    issue_comments = data.get("issue_comments")
    review_count = len(review_comments) if isinstance(review_comments, list) else 0
    issue_count = len(issue_comments) if isinstance(issue_comments, list) else 0
    return f"review_comments={review_count}\nissue_comments={issue_count}"


def _collect_threads(data: object) -> list[dict[str, object]]:
    threads = (
        data.get("data", {})
        .get("repository", {})
        .get("pullRequest", {})
        .get("reviewThreads", {})
        .get("nodes", [])
        if isinstance(data, dict)
        else []
    )
    return [thread for thread in threads if isinstance(thread, dict)]


def _matches_state(thread: dict[str, object], state: str) -> bool:
    is_resolved = bool(thread.get("isResolved", False))
    is_outdated = bool(thread.get("isOutdated", False))
    if state == "all":
        return True
    if state == "resolved":
        return is_resolved
    if state == "outdated":
        return is_outdated
    return not is_resolved and not is_outdated


def _line_range(thread: dict[str, object]) -> str:
    start = thread.get("startLine")
    line = thread.get("line")
    if isinstance(start, int) and isinstance(line, int):
        return f"L{start}-L{line}"
    if isinstance(line, int):
        return f"L{line}"
    return "L?"


def format_threads_review(
    data: object,
    *,
    state: str,
    show_pr: bool,
    include_author: bool,
    include_url: bool,
    ref: pr_ref.PullRequestRef,
) -> str:
    lines: list[str] = []
    if show_pr:
        lines.append(f"PR: {ref.owner}/{ref.repo}#{ref.number}")
    for thread in _collect_threads(data):
        if not _matches_state(thread, state):
            continue
        lines.append("---")
        path = (
            thread.get("path") if isinstance(thread.get("path"), str) else "<unknown>"
        )
        lines.append(f"{path}:{_line_range(thread)}")
        diff_hunk = thread.get("diffHunk")
        if isinstance(diff_hunk, str) and diff_hunk:
            lines.append("```diff")
            lines.append(diff_hunk)
            lines.append("```")
        comments = thread.get("comments", {})
        nodes = comments.get("nodes", []) if isinstance(comments, dict) else []
        if nodes and isinstance(nodes[-1], dict):
            latest = nodes[-1]
            body = latest.get("body") if isinstance(latest.get("body"), str) else ""
            lines.append(body)
            author = (
                latest.get("author") if isinstance(latest.get("author"), dict) else {}
            )
            if include_author and isinstance(author.get("login"), str):
                lines.append(f"author: {author['login']}")
            if include_url and isinstance(latest.get("url"), str):
                lines.append(f"url: {latest['url']}")
    if not lines:
        return ""
    return "\n".join(lines)


def format_threads_raw(
    data: object, *, state: str, show_pr: bool, ref: pr_ref.PullRequestRef
) -> str:
    payload: dict[str, object] = {
        "threads": [t for t in _collect_threads(data) if _matches_state(t, state)],
    }
    if show_pr:
        payload["pull_request"] = {
            "owner": ref.owner,
            "repo": ref.repo,
            "number": ref.number,
        }
    return json.dumps(payload, indent=2, sort_keys=True)


def has_threads_for_state(data: object, *, state: str) -> bool:
    """Return whether at least one review thread matches the requested state."""
    for thread in _collect_threads(data):
        if _matches_state(thread, state):
            return True
    return False
