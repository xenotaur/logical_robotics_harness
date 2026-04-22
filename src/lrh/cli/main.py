"""Initial CLI entrypoint for Logical Robotics Harness."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lrh.assist import request_cli, snapshot_cli, sourcetree_surveyor
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

    subparsers.add_parser(
        "survey",
        add_help=False,
        help="Survey a Python source tree for assist planning workflows.",
    )

    meta_parser = subparsers.add_parser(
        "meta",
        help="Manage LRH workspace/meta-control state.",
    )
    meta_subparsers = meta_parser.add_subparsers(dest="meta_command")

    def _add_meta_workspace_resolution_args(
        target_parser: argparse.ArgumentParser,
    ) -> None:
        target_parser.add_argument(
            "--workspace",
            help="explicit local workspace root containing .lrh/config.toml",
        )
        target_parser.add_argument(
            "--config",
            help="explicit workspace config.toml path",
        )
        target_parser.add_argument(
            "--mode",
            choices=("local", "global"),
            help="workspace mode override for resolution",
        )

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
    _add_meta_workspace_resolution_args(meta_subparsers.choices["list"])
    meta_register_parser = meta_subparsers.add_parser(
        "register",
        help="Register a project repository in the workspace registry.",
    )
    _add_meta_workspace_resolution_args(meta_register_parser)
    meta_register_parser.add_argument(
        "repo_locator",
        help="repository locator string (local path, URL, or other stable locator)",
    )
    meta_register_parser.add_argument(
        "--project-dir",
        default="project",
        help="project control directory relative to the repo root (default: project)",
    )
    meta_register_parser.add_argument(
        "--directory-name",
        help="registry directory name under projects/ (default: inferred from locator)",
    )
    meta_register_parser.add_argument(
        "--short-name",
        help="short display label (default: directory name)",
    )
    meta_register_parser.add_argument(
        "--display-name",
        help="human-readable project name (default: inferred from short name)",
    )
    meta_register_parser.add_argument(
        "--force",
        action="store_true",
        help="allow deliberate duplicates and overwrite existing target records",
    )

    if sys.argv[1:] == ["help"]:
        parser.print_help()
        raise SystemExit(0)

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

    if args.command == "survey":
        raise SystemExit(
            sourcetree_surveyor.main(
                argv=passthrough_args,
                prog="lrh survey",
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
                active_workspace = workspace.resolve_meta_workspace(
                    cwd=Path.cwd(),
                    options=workspace.MetaWorkspaceResolveOptions(
                        workspace_path=(
                            Path(args.workspace).expanduser()
                            if args.workspace
                            else None
                        ),
                        config_path=(
                            Path(args.config).expanduser() if args.config else None
                        ),
                        mode=args.mode,
                    ),
                )
                records = workspace.list_registered_projects_in_workspace(
                    active_workspace
                )
            except (
                workspace.MetaWorkspaceResolutionError,
                workspace.MetaRegistryError,
            ) as err:
                print(f"error: {err}")
                raise SystemExit(1) from err

            print(workspace.format_project_records(records))
            raise SystemExit(0)

        if args.meta_command == "register":
            if passthrough_args:
                parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")
            spec = workspace.MetaRegisterSpec(
                repo_locator=args.repo_locator,
                project_dir=args.project_dir,
                directory_name=args.directory_name,
                short_name=args.short_name,
                display_name=args.display_name,
            )
            try:
                active_workspace = workspace.resolve_meta_workspace(
                    cwd=Path.cwd(),
                    options=workspace.MetaWorkspaceResolveOptions(
                        workspace_path=(
                            Path(args.workspace).expanduser()
                            if args.workspace
                            else None
                        ),
                        config_path=(
                            Path(args.config).expanduser() if args.config else None
                        ),
                        mode=args.mode,
                    ),
                )
                result = workspace.register_project_in_workspace(
                    active_workspace,
                    spec=spec,
                    force=args.force,
                )
            except (
                workspace.MetaWorkspaceResolutionError,
                workspace.MetaRegistryError,
            ) as err:
                print(f"error: {err}")
                raise SystemExit(1) from err

            print(f"Registered project in {result.record_path}")
            print(f"project_id={result.project_id}")
            print(f"setup_state={result.setup_state}")
            raise SystemExit(0)

        parser.error("meta requires a subcommand (try: lrh meta init)")

    if passthrough_args:
        parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")

    print("Logical Robotics Harness bootstrap CLI")


if __name__ == "__main__":
    main()
