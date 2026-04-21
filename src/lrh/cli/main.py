"""Initial CLI entrypoint for Logical Robotics Harness."""

from __future__ import annotations

import argparse
from pathlib import Path

from lrh.assist import request_cli, snapshot_cli
from lrh.control import format_report, validate_project


def _default_request_template_root() -> Path:
    """Resolve request templates from the repository scripts path."""
    return Path("scripts/aiprog/templates/request").resolve()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="lrh",
        description="Logical Robotics Harness command-line interface.",
    )
    subparsers = parser.add_subparsers(dest="command")

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate project control files.",
    )
    validate_parser.add_argument(
        "--project-dir",
        default="project",
        help="path to the project control directory (default: project)",
    )

    subparsers.add_parser(
        "request",
        add_help=False,
        help="Render an assist request from a template.",
    )

    subparsers.add_parser(
        "snapshot",
        add_help=False,
        help="Generate assist snapshot context packets.",
    )

    args, passthrough_args = parser.parse_known_args()

    if args.command == "validate":
        if passthrough_args:
            parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")
        report = validate_project(Path(args.project_dir))
        print(format_report(report))
        raise SystemExit(1 if report.errors else 0)

    if args.command == "request":
        raise SystemExit(
            request_cli.run_request_cli(
                argv=passthrough_args,
                template_root=_default_request_template_root(),
                prog="lrh request",
            )
        )

    if args.command == "snapshot":
        raise SystemExit(
            snapshot_cli.run_snapshot_cli(
                argv=passthrough_args,
                prog="lrh snapshot",
            )
        )

    if passthrough_args:
        parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")

    print("Logical Robotics Harness bootstrap CLI")


if __name__ == "__main__":
    main()
