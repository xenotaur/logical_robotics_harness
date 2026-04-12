"""Initial CLI entrypoint for Logical Robotics Harness."""

from __future__ import annotations

import argparse
from pathlib import Path

from lrh.control import format_report, validate_project


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

    args = parser.parse_args()

    if args.command == "validate":
        report = validate_project(Path(args.project_dir))
        print(format_report(report))
        raise SystemExit(1 if report.errors else 0)

    print("Logical Robotics Harness bootstrap CLI")


if __name__ == "__main__":
    main()
