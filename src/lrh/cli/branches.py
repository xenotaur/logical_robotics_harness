"""CLI handler for `lrh branches`.

A new top-level command group, not an extension of `github` or
`sessions` (the two alternatives the work item weighed): `github` is
about PR comments/threads on a specific pull request, and `sessions` is
about the private session archive -- neither is about local branch
state. `branches` follows the same passthrough-dispatch pattern as
`github`/`survey`/`serve` (see `src/lrh/cli/main.py`): a self-contained
argparse handler invoked with the process's remaining argv.
"""

from __future__ import annotations

import argparse
import json
import pathlib

from lrh import branch_hygiene


def _run_survey(args: argparse.Namespace) -> int:
    try:
        infos = branch_hygiene.survey_local_branches(project_root=args.project_root)
    except branch_hygiene.BranchHygieneError as error:
        print(str(error))
        return 1

    if args.format == "json":
        payload = [
            {
                "name": info.name,
                "class": info.branch_class.value,
                "delete_flag": info.delete_flag,
                "reason": info.reason,
                "has_upstream": info.has_upstream,
                "open_pr_numbers": list(info.open_pr_numbers),
                "merged_pr_number": info.merged_pr_number,
            }
            for info in infos
        ]
        print(json.dumps(payload, indent=2))
    else:
        print(branch_hygiene.render_report_markdown(infos))

    if args.write_delete_commands is not None:
        content = branch_hygiene.render_delete_commands_file(infos)
        path = pathlib.Path(args.write_delete_commands)
        path.write_text(content, encoding="utf-8")
        print(f"Wrote reviewable delete commands to {path}")

    return 0


def run_branches_cli(argv: list[str], prog: str) -> int:
    parser = argparse.ArgumentParser(prog=prog)
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    survey_parser = subparsers.add_parser(
        "survey",
        help="Classify local branches (report-only; never deletes anything).",
    )
    survey_parser.add_argument(
        "--format",
        choices=["md", "json"],
        default="md",
        help="Report output format. Defaults to md.",
    )
    survey_parser.add_argument(
        "--write-delete-commands",
        metavar="PATH",
        default=None,
        help=(
            "Write reviewable `git branch` delete commands to PATH for a "
            "human to inspect and run. This command never executes them "
            "itself."
        ),
    )
    survey_parser.add_argument(
        "--project-root",
        default=".",
        help="Repository root to survey. Defaults to the current directory.",
    )

    args = parser.parse_args(argv)
    if args.subcommand == "survey":
        return _run_survey(args)
    parser.error(f"unknown subcommand: {args.subcommand}")
    return 2
