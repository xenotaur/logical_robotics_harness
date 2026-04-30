"""CLI handler for `lrh github`."""

from __future__ import annotations

import argparse
import json

from lrh.integrations.github import formatters, pr_ref, pull_reviews


def _parse_target(target: str, number: int | None) -> pr_ref.PullRequestRef:
    if target.startswith("http://") or target.startswith("https://"):
        return pr_ref.parse_pull_request_url(target)
    if number is None:
        raise ValueError("number is required when target is OWNER/REPO")
    return pr_ref.parse_pull_request_ref(target, number)


def _render_threads(args: argparse.Namespace, ref: pr_ref.PullRequestRef) -> str:
    data = pull_reviews.get_pull_review_threads(ref)
    state = "unresolved" if args.kind == "unresolved" else args.state
    if args.mode == "raw":
        return formatters.format_threads_raw(
            data, state=state, show_pr=args.show_pr, ref=ref
        )
    return formatters.format_threads_review(
        data,
        state=state,
        show_pr=args.show_pr,
        include_author=True,
        include_url=True,
        ref=ref,
    )


def run_github_cli(argv: list[str], prog: str) -> int:
    parser = argparse.ArgumentParser(prog=prog)
    parser.add_argument("kind", choices=["comments", "threads", "unresolved"])
    parser.add_argument("target")
    parser.add_argument("number", nargs="?", type=int)
    parser.add_argument("--mode", choices=["review", "raw"], default="review")
    parser.add_argument(
        "--state",
        choices=["unresolved", "resolved", "outdated", "all"],
        default="all",
    )
    parser.add_argument("--show-pr", dest="show_pr", action="store_true", default=True)
    parser.add_argument("--no-show-pr", dest="show_pr", action="store_false")
    args = parser.parse_args(argv)

    try:
        ref = _parse_target(args.target, args.number)
    except ValueError as err:
        parser.error(str(err))
    if args.kind == "comments":
        data = pull_reviews.get_pull_comments(ref)
        if args.mode == "raw":
            print(json.dumps(data, indent=2, sort_keys=True))
        else:
            print(formatters.format_comments(data))
    else:
        print(_render_threads(args, ref))
    return 0
