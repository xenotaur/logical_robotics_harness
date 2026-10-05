"""CLI handler for `lrh vcs`."""

from __future__ import annotations

import argparse
import json
import sys

from lrh.vcs import backend, registry


def _build_parser(prog: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description=(
            "Backend-neutral VCS actions that LRH skills perform after their gates."
        ),
    )
    subparsers = parser.add_subparsers(dest="vcs_command", required=True)
    merge_parser = subparsers.add_parser(
        "merge",
        help="Merge a pull request only at an exact, previously verified head commit.",
        description=(
            "Refuses unless the pull request is open and its head is exactly "
            "--match-head-commit, issues the merge once without retrying, then "
            "reads the pull request back. Exit 0: confirmed merged. Exit 1: "
            "merge accepted but not yet merged (for example queued). Exit 2: "
            "refused or failed; if the merge command itself failed, the message "
            "also reports the pull request's state afterwards."
        ),
    )
    merge_parser.add_argument("pr", help="pull request URL")
    mode_group = merge_parser.add_mutually_exclusive_group(required=True)
    for mode in backend.MERGE_MODES:
        mode_group.add_argument(
            f"--{mode}",
            dest="mode",
            action="store_const",
            const=mode,
            help=f"merge method: {mode}",
        )
    merge_parser.add_argument(
        "--match-head-commit",
        required=True,
        metavar="SHA",
        help="full 40-character head SHA the merge must apply to",
    )
    merge_parser.add_argument(
        "--backend",
        choices=registry.backend_names(),
        default=registry.DEFAULT_BACKEND,
        help=f"VCS backend (default: {registry.DEFAULT_BACKEND})",
    )
    merge_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format (default: text)",
    )
    return parser


def _run_merge(args: argparse.Namespace) -> int:
    try:
        vcs_backend = registry.create_backend(args.backend)
        outcome = backend.merge_pull_request_locked(
            vcs_backend,
            args.pr,
            mode=args.mode,
            match_head_commit=args.match_head_commit,
        )
    except backend.MergeRefusedError as err:
        print(f"refused: {err}", file=sys.stderr)
        return 2
    except backend.VcsError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(
            json.dumps(
                {
                    "status": outcome.status,
                    "state": outcome.state,
                    "merge_commit": outcome.merge_commit,
                    "backend": args.backend,
                    "pr": args.pr,
                },
                sort_keys=True,
            )
        )
    elif outcome.status == "merged":
        print(f"merged: {outcome.merge_commit or '(merge commit not reported)'}")
    else:
        print(
            f"queued: the merge was accepted but the pull request is still "
            f"{outcome.state}; re-check its state before proceeding"
        )
    return 0 if outcome.status == "merged" else 1


def run_vcs_cli(argv: list[str], prog: str) -> int:
    """Run `lrh vcs` and return the process exit code."""
    args = _build_parser(prog).parse_args(argv)
    if args.vcs_command == "merge":
        return _run_merge(args)
    raise AssertionError(f"unhandled vcs command: {args.vcs_command}")
