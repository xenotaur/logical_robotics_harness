"""Initial CLI entrypoint for Logical Robotics Harness."""

from __future__ import annotations

import argparse
from pathlib import Path

from lrh.assist import request_cli
from lrh.control import format_report, validate_project


def _default_request_template_root() -> Path:
    """Resolve request templates from the repository scripts path."""
    return Path("scripts/aiprog/templates/request").resolve()


def main() -> None:
    parser = argparse.ArgumentParser(prog="lrh")
    subparsers = parser.add_subparsers(dest="command")

    validate_parser = subparsers.add_parser(
        "validate", help="validate the project directory"
    )
    validate_parser.add_argument(
        "--project-dir",
        default="project",
        help="path to the project control directory (default: project)",
    )

    request_parser = subparsers.add_parser(
        "request", help="render an assist request from a template"
    )
    request_parser.add_argument(
        "request_args",
        nargs=argparse.REMAINDER,
        help="arguments passed through to the request command",
    )

    args = parser.parse_args()

    if args.command == "validate":
        report = validate_project(Path(args.project_dir))
        print(format_report(report))
        raise SystemExit(1 if report.errors else 0)

    if args.command == "request":
        raise SystemExit(
            request_cli.run_request_cli(
                argv=args.request_args,
                template_root=_default_request_template_root(),
                prog="lrh request",
            )
        )

    print("Logical Robotics Harness bootstrap CLI")


if __name__ == "__main__":
    main()
