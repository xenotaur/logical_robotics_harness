"""CLI handler for `lrh github`."""

from __future__ import annotations

import argparse

from lrh.integrations.github import formatters, pr_ref, pull_reviews


def run_github_cli(argv: list[str], prog: str) -> int:
    parser = argparse.ArgumentParser(prog=prog)
    parser.add_argument("kind", choices=["comments", "threads", "unresolved"])
    parser.add_argument("repo")
    parser.add_argument("number", type=int)
    args = parser.parse_args(argv)

    ref = pr_ref.parse_pull_request_ref(args.repo, args.number)
    if args.kind == "comments":
        print(formatters.format_comments(pull_reviews.get_pull_comments(ref)))
    elif args.kind == "threads":
        print(formatters.format_threads(pull_reviews.get_pull_review_threads(ref)))
    else:
        print(formatters.format_threads(pull_reviews.get_pull_review_threads(ref)))
    return 0
