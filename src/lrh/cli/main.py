"""Initial CLI entrypoint for Logical Robotics Harness."""

from __future__ import annotations

import argparse
import json
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
    validate_parser.add_argument(
        "--work-items",
        action="store_true",
        help="validate work-item files and policy rules only",
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
        description=(
            "Manage LRH meta workspaces and project registry records. "
            "Workspace resolution precedence: flags, LRH_CONFIG, LRH_WORKSPACE, "
            "local discovery, then global discovery/defaults."
        ),
        epilog=(
            "Global defaults when XDG variables are unset:\n"
            "  config: ~/.config/lrh/config.toml\n"
            "  state: ~/.local/state/lrh/\n"
            "  cache: ~/.cache/lrh/"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
        help="Initialize LRH meta workspace paths (defaults to global mode).",
        description=(
            "Initialize LRH meta workspace directories and config. "
            "Default mode is global (XDG-style user paths); use --mode local "
            "to initialize a local workspace in the current directory."
        ),
        epilog=(
            "Resolution inputs (high-level): flags, LRH_CONFIG, LRH_WORKSPACE, "
            "local workspace discovery, global workspace discovery.\n\n"
            "Global defaults when XDG variables are unset:\n"
            "  config: ~/.config/lrh/config.toml\n"
            "  state: ~/.local/state/lrh/\n"
            "  cache: ~/.cache/lrh/"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    meta_init_parser.add_argument(
        "--name",
        default="LRH Workspace",
        help="workspace display name for generated README/config",
    )
    meta_init_parser.add_argument(
        "--mode",
        choices=("global", "local"),
        default="global",
        help="initialization mode (default: global)",
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

    meta_where_parser = meta_subparsers.add_parser(
        "where",
        help="Show the active workspace and how it was resolved.",
    )
    _add_meta_workspace_resolution_args(meta_where_parser)
    meta_where_parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON for the active workspace",
    )
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
        help=(
            "project control directory relative to repo root "
            "(default: inferred for supported URL patterns, otherwise project)"
        ),
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
    meta_inspect_parser = meta_subparsers.add_parser(
        "inspect",
        help="Inspect one registered project with workspace context.",
    )
    _add_meta_workspace_resolution_args(meta_inspect_parser)
    meta_inspect_parser.add_argument(
        "project",
        help="project selector (exact project_id, short_name, or registry_name)",
    )

    argv = sys.argv[1:]
    if argv and argv[0] == "help":
        if len(argv) == 1:
            parser.print_help()
            raise SystemExit(0)
        argv = [*argv[1:], "--help"]

    args, passthrough_args = parser.parse_known_args(argv)

    if args.command == "validate":
        if passthrough_args:
            parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")
        report = validate_project(
            Path(args.project_dir),
            work_items_only=args.work_items,
        )
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
                if args.mode == "local":
                    result = workspace.init_workspace(
                        Path.cwd(),
                        spec=spec,
                        force=args.force,
                    )
                else:
                    result = workspace.init_global_workspace(
                        spec=spec,
                        force=args.force,
                    )
            except workspace.MetaInitError as err:
                print(f"error: {err}")
                raise SystemExit(1) from err

            if args.mode == "local":
                print("Initialized LRH local meta workspace at", Path.cwd())
            else:
                print("Initialized LRH global meta workspace")
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

        if args.meta_command == "where":
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
            except workspace.MetaWorkspaceResolutionError as err:
                print(f"error: {err}")
                raise SystemExit(1) from err

            workspace_data: dict[str, str | None] = {
                "mode": active_workspace.mode,
                "resolution_source": active_workspace.resolution_source,
                "config_path": str(active_workspace.config_path),
                "projects_dir": str(active_workspace.projects_dir),
                "state_dir": str(active_workspace.state_dir),
                "cache_dir": str(active_workspace.cache_dir),
                "workspace_root": (
                    str(active_workspace.workspace_root)
                    if active_workspace.workspace_root is not None
                    else None
                ),
            }
            if args.json:
                print(json.dumps(workspace_data, indent=2, sort_keys=True))
            else:
                print("Active LRH meta workspace")
                print()
                print(f"mode: {workspace_data['mode']}")
                print(f"resolution source: {workspace_data['resolution_source']}")
                print(f"config: {workspace_data['config_path']}")
                print(f"projects: {workspace_data['projects_dir']}")
                print(f"state: {workspace_data['state_dir']}")
                print(f"cache: {workspace_data['cache_dir']}")
                if workspace_data["workspace_root"] is not None:
                    print(f"workspace root: {workspace_data['workspace_root']}")
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

        if args.meta_command == "inspect":
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
                inspect_result = workspace.inspect_registered_project_in_workspace(
                    active_workspace,
                    selector=args.project,
                )
            except (
                workspace.MetaWorkspaceResolutionError,
                workspace.MetaRegistryError,
            ) as err:
                print(f"error: {err}")
                raise SystemExit(1) from err
            print(workspace.format_project_inspect(inspect_result))
            raise SystemExit(0)

        parser.error("meta requires a subcommand (try: lrh meta init)")

    if passthrough_args:
        parser.error(f"unrecognized arguments: {' '.join(passthrough_args)}")

    print("Logical Robotics Harness bootstrap CLI")


if __name__ == "__main__":
    main()
