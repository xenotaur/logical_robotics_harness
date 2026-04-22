"""Initial CLI entrypoint for Logical Robotics Harness."""

from __future__ import annotations

import argparse
from pathlib import Path

from lrh.assist import request_cli, snapshot_cli
from lrh.control import format_report, validate_project
from lrh.meta import workspace


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

    meta_parser = subparsers.add_parser(
        "meta",
        help="Manage LRH workspace/meta-control state.",
    )
    meta_subparsers = meta_parser.add_subparsers(dest="meta_command")

    meta_init_parser = meta_subparsers.add_parser(
        "init",
        help="Initialize an LRH workspace layout in the current directory.",
    )
    meta_init_parser.add_argument(
        "--name",
        default="LRH Workspace",
        help="workspace display name for generated README/config",
    )
    meta_init_parser.add_argument(
        "--force",
        action="store_true",
        help="replace incompatible managed paths/content when safe",
    )

    meta_subparsers.add_parser(
        "list",
        help="List registered projects from the workspace registry.",
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

    if args.command == "meta":
        if args.meta_command == "init":
            if passthrough_args:
                parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")
            spec = workspace.MetaWorkspaceSpec(workspace_name=args.name)
            try:
                result = workspace.init_workspace(
                    Path.cwd(),
                    spec=spec,
                    force=args.force,
                )
            except workspace.MetaInitError as err:
                print(f"error: {err}")
                raise SystemExit(1) from err

            print("Initialized LRH meta workspace at", Path.cwd())
            print(
                f"created={len(result.created)} "
                f"updated={len(result.updated)} "
                f"unchanged={len(result.unchanged)}"
            )
            raise SystemExit(0)

        if args.meta_command == "list":
            if passthrough_args:
                parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")
            try:
                records = workspace.list_registered_projects(Path.cwd())
            except workspace.MetaRegistryError as err:
                print(f"error: {err}")
                raise SystemExit(1) from err

            print(workspace.format_project_records(records))
            raise SystemExit(0)

        parser.error("meta requires a subcommand (try: lrh meta init)")

    if passthrough_args:
        parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")

    print("Logical Robotics Harness bootstrap CLI")


if __name__ == "__main__":
    main()
