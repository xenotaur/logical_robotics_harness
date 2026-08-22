"""``lrh sessions`` CLI: sync, discover, link, report, closeout-sync, schedule.

PROP-LRH-SESSION-ARCHIVE-SYNC Stage 2 added sync/discover/link. Stage 3 adds
the metadata-only report command. Stage 4 adds closeout-triggered sync wiring
and a documented, inspectable weekly launchd schedule path. This module stays
as thin CLI wiring over the core logic in ``prompt_workflow_sessions`` rather
than being folded into that module: ``link`` needs
``prompt_workflow.write_session_transcript_field`` and
``prompt_workflow.find_execution_record_by_id``, while ``prompt_workflow.py``
already imports ``prompt_workflow_sessions`` for ``record-session-alias``.
"""

from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import plistlib
import shlex
import sys

from lrh import prompt_workflow, prompt_workflow_sessions


def _utc_now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _default_claude_projects_root() -> pathlib.Path:
    return pathlib.Path.home() / ".claude" / "projects"


def run_sessions_cli(argv: list[str], *, prog: str = "lrh sessions") -> int:
    parser = argparse.ArgumentParser(
        prog=prog, description="Session archive reconciler."
    )
    subparsers = parser.add_subparsers(dest="sessions_command")

    sync_parser = subparsers.add_parser(
        "sync",
        help=(
            "Mirror local Claude Code transcripts into a durable archive and, "
            "if --exports-dir is given, harvest /export metadata.json "
            "identity fields into project/sessions/index.jsonl."
        ),
    )
    sync_parser.add_argument(
        "--claude-projects-root",
        default=None,
        help="root to scan for */*.jsonl transcripts (default: ~/.claude/projects)",
    )
    sync_parser.add_argument(
        "--exports-dir",
        default=None,
        help=(
            "directory of session-export-*.zip files to harvest; omit to skip "
            "export harvest entirely (no default location is assumed)"
        ),
    )
    sync_parser.add_argument(
        "--archive-root",
        default=None,
        help=(
            "local archive root (default: $LRH_SESSION_ARCHIVE_ROOT, else "
            "~/.local/share/lrh/session-archive)"
        ),
    )
    sync_parser.add_argument("--project-root", default=".")
    sync_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would be mirrored/harvested without writing anything",
    )

    closeout_sync_parser = subparsers.add_parser(
        "closeout-sync",
        help=(
            "Run the session archive sync path intended for /lrh-closeout and "
            "print a human-visible outcome."
        ),
    )
    _add_sync_arguments(closeout_sync_parser)
    closeout_sync_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would be mirrored/harvested without writing anything",
    )

    schedule_parser = subparsers.add_parser(
        "schedule",
        help=(
            "Render or write an inspectable weekly launchd plist for "
            "`lrh sessions sync`."
        ),
    )
    schedule_parser.add_argument("--project-root", default=".")
    schedule_parser.add_argument("--claude-projects-root", default=None)
    schedule_parser.add_argument("--exports-dir", default=None)
    schedule_parser.add_argument("--archive-root", default=None)
    schedule_parser.add_argument(
        "--lrh-command",
        default="lrh",
        help=(
            "lrh executable to put in the schedule command; use an absolute path "
            "for launchd if PATH is not configured"
        ),
    )
    schedule_parser.add_argument(
        "--label",
        default=None,
        help="launchd label (default: org.lrh.sessions.<project-slug>)",
    )
    schedule_parser.add_argument(
        "--weekday",
        type=int,
        default=1,
        choices=range(0, 8),
        metavar="0-7",
        help="launchd weekday for weekly sync, where 0 or 7 is Sunday (default: 1)",
    )
    schedule_parser.add_argument(
        "--hour",
        type=int,
        default=9,
        choices=range(0, 24),
        metavar="0-23",
        help="launchd hour for weekly sync (default: 9)",
    )
    schedule_parser.add_argument(
        "--minute",
        type=int,
        default=0,
        choices=range(0, 60),
        metavar="0-59",
        help="launchd minute for weekly sync (default: 0)",
    )
    schedule_parser.add_argument(
        "--output",
        default=None,
        help="write plist to this path instead of stdout",
    )

    discover_parser = subparsers.add_parser(
        "discover",
        help=(
            "List local transcripts for the current project, cross-referenced "
            "against the index."
        ),
    )
    discover_parser.add_argument(
        "--claude-projects-root",
        default=None,
        help="root to scan (default: ~/.claude/projects)",
    )
    discover_parser.add_argument(
        "--project-path",
        default=None,
        help="path to slug (default: --project-root)",
    )
    discover_parser.add_argument("--project-root", default=".")
    discover_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
    )

    link_parser = subparsers.add_parser(
        "link",
        help=(
            "Promote a resolved child id to its host-keyed session_transcript "
            "pointer on an execution record."
        ),
    )
    link_parser.add_argument("--execution-id", required=True)
    link_parser.add_argument("--child-id", required=True)
    link_parser.add_argument("--project-root", default=".")

    report_parser = subparsers.add_parser(
        "report",
        help=(
            "Report execution-record session pointers that are pending, "
            "dangling, or missing durable private archive coverage."
        ),
    )
    report_parser.add_argument(
        "--archive-root",
        default=None,
        help=(
            "local archive root (default: $LRH_SESSION_ARCHIVE_ROOT, else "
            "~/.local/share/lrh/session-archive)"
        ),
    )
    report_parser.add_argument("--project-root", default=".")
    report_parser.add_argument(
        "--since-created-at",
        default=None,
        help=(
            "only include execution records with created_at at or after this "
            "ISO timestamp"
        ),
    )
    report_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
    )

    args = parser.parse_args(argv)
    if args.sessions_command is None:
        parser.error("sessions requires a subcommand (try: lrh sessions discover)")

    if args.sessions_command == "sync":
        return _run_sync(args)
    if args.sessions_command == "closeout-sync":
        return _run_closeout_sync(args)
    if args.sessions_command == "schedule":
        return _run_schedule(args)
    if args.sessions_command == "discover":
        return _run_discover(args)
    if args.sessions_command == "link":
        return _run_link(args)
    if args.sessions_command == "report":
        return _run_report(args)
    parser.error("sessions requires a subcommand (try: lrh sessions discover)")
    return 2  # pragma: no cover -- parser.error raises SystemExit


def _add_sync_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--claude-projects-root",
        default=None,
        help="root to scan for */*.jsonl transcripts (default: ~/.claude/projects)",
    )
    parser.add_argument(
        "--exports-dir",
        default=None,
        help=(
            "directory of session-export-*.zip files to harvest; omit to skip "
            "export harvest entirely (no default location is assumed)"
        ),
    )
    parser.add_argument(
        "--archive-root",
        default=None,
        help=(
            "local archive root (default: $LRH_SESSION_ARCHIVE_ROOT, else "
            "~/.local/share/lrh/session-archive)"
        ),
    )
    parser.add_argument("--project-root", default=".")


def _run_sync(args: argparse.Namespace) -> int:
    claude_projects_root = (
        pathlib.Path(args.claude_projects_root).expanduser()
        if args.claude_projects_root
        else _default_claude_projects_root()
    )
    archive_root = prompt_workflow_sessions.resolve_archive_root(args.archive_root)
    updated_at = _utc_now_iso()

    transcripts = prompt_workflow_sessions.discover_transcripts(claude_projects_root)
    mirrored = 0
    aliases_added = 0
    for transcript in transcripts:
        if args.dry_run:
            print(
                f"would mirror: {transcript.path} -> "
                f"{archive_root / 'raw' / transcript.slug / transcript.relative_path}"
            )
            continue
        result = prompt_workflow_sessions.mirror_transcript(
            transcript.path,
            archive_root,
            project_slug=transcript.slug,
            relative_path=transcript.relative_path,
        )
        if result.copied:
            mirrored += 1
            print(f"mirrored: {transcript.path} -> {result.dest}")
        # Independent of whether the raw copy changed: fold in any
        # line-level sessionId aliases this transcript reveals for an
        # already-known host, so a forked lineage's aliases (which can
        # appear in no filename anywhere) are not left incomplete.
        if transcript.is_top_level:
            reconciled = prompt_workflow_sessions.reconcile_child_id_aliases(
                args.project_root, transcript.path, updated_at=updated_at
            )
            if reconciled is not None:
                host_id, new_aliases = reconciled
                aliases_added += len(new_aliases)
                print(
                    f"aliased: {transcript.path} -> host_id={host_id} "
                    f"(+{len(new_aliases)} child id(s))"
                )

    harvested = 0
    if args.exports_dir:
        exports_dir = pathlib.Path(args.exports_dir).expanduser()
        for export_zip in sorted(exports_dir.glob("session-export-*.zip")):
            if args.dry_run:
                print(f"would harvest: {export_zip}")
                continue
            try:
                record = prompt_workflow_sessions.sync_export(
                    args.project_root,
                    archive_root,
                    export_zip,
                    updated_at=updated_at,
                )
            except prompt_workflow_sessions.ExportMetadataError as error:
                print(f"skipped {export_zip}: {error}", file=sys.stderr)
                continue
            if record is not None:
                harvested += 1
                print(f"harvested: {export_zip} -> host_id={record.host_id}")

    if args.dry_run:
        harvest_note = "enabled" if args.exports_dir else "skipped (no --exports-dir)"
        print(
            f"dry-run: {len(transcripts)} transcript(s) considered, "
            f"export harvest {harvest_note}"
        )
    else:
        print(
            f"sync complete: {mirrored} transcript(s) mirrored, "
            f"{harvested} export(s) harvested, {aliases_added} child-id "
            f"alias(es) reconciled"
        )
    return 0


def _run_closeout_sync(args: argparse.Namespace) -> int:
    print("closeout session archive sync")
    try:
        exit_code = _run_sync(args)
    except (OSError, ValueError) as error:
        print(f"error: closeout-sync failed: {error}", file=sys.stderr)
        return 1
    if exit_code == 0:
        print("closeout-sync complete")
    return exit_code


def _run_schedule(args: argparse.Namespace) -> int:
    plist = build_launchd_plist(
        project_root=args.project_root,
        claude_projects_root=args.claude_projects_root,
        exports_dir=args.exports_dir,
        archive_root=args.archive_root,
        lrh_command=args.lrh_command,
        label=args.label,
        weekday=args.weekday,
        hour=args.hour,
        minute=args.minute,
    )
    payload = plistlib.dumps(plist, sort_keys=True).decode("utf-8")
    if args.output:
        output_path = pathlib.Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload, encoding="utf-8")
        print(f"wrote: {output_path}")
    else:
        print(payload, end="")
    return 0


def build_launchd_plist(
    *,
    project_root: str | pathlib.Path,
    claude_projects_root: str | pathlib.Path | None = None,
    exports_dir: str | pathlib.Path | None = None,
    archive_root: str | pathlib.Path | None = None,
    lrh_command: str = "lrh",
    label: str | None = None,
    weekday: int = 1,
    hour: int = 9,
    minute: int = 0,
) -> dict[str, object]:
    """Build an inspectable weekly launchd plist for ``lrh sessions sync``."""

    project_path = pathlib.Path(project_root).expanduser().resolve()
    resolved_label = label or (
        "org.lrh.sessions."
        f"{prompt_workflow_sessions.project_slug_for_path(project_path).strip('-')}"
    )
    command_parts = [
        lrh_command,
        "sessions",
        "sync",
        "--project-root",
        str(project_path),
    ]
    if claude_projects_root:
        command_parts.extend(
            [
                "--claude-projects-root",
                str(pathlib.Path(claude_projects_root).expanduser()),
            ]
        )
    if exports_dir:
        command_parts.extend(
            ["--exports-dir", str(pathlib.Path(exports_dir).expanduser())]
        )
    if archive_root:
        command_parts.extend(
            ["--archive-root", str(pathlib.Path(archive_root).expanduser())]
        )
    command = " ".join(shlex.quote(part) for part in command_parts)
    return {
        "Label": resolved_label,
        "ProgramArguments": ["/bin/sh", "-lc", command],
        "StartCalendarInterval": {
            "Weekday": weekday,
            "Hour": hour,
            "Minute": minute,
        },
        "RunAtLoad": False,
        "StandardOutPath": str(project_path / ".lrh-sessions-sync.out.log"),
        "StandardErrorPath": str(project_path / ".lrh-sessions-sync.err.log"),
        "WorkingDirectory": str(project_path),
    }


def _run_discover(args: argparse.Namespace) -> int:
    claude_projects_root = (
        pathlib.Path(args.claude_projects_root).expanduser()
        if args.claude_projects_root
        else _default_claude_projects_root()
    )
    sessions = prompt_workflow_sessions.discover_sessions_for_project(
        args.project_root,
        claude_projects_root,
        project_path=args.project_path,
    )
    if args.format == "json":
        print(
            json.dumps(
                [
                    {
                        "child_id": s.child_id,
                        "path": str(s.path),
                        "size_bytes": s.size_bytes,
                        "mtime": s.mtime,
                        "host_id": s.host_id,
                    }
                    for s in sessions
                ],
                indent=2,
            )
        )
        return 0
    if not sessions:
        print("no local transcripts found for this project")
        return 0
    for session in sessions:
        host = session.host_id or "(unresolved)"
        print(
            f"{session.child_id}\thost={host}\tsize={session.size_bytes}\t{session.path}"
        )
    return 0


def _run_link(args: argparse.Namespace) -> int:
    try:
        host_id = prompt_workflow_sessions.resolve_host_id_for_child(
            args.project_root, args.child_id
        )
    except prompt_workflow_sessions.LinkLookupError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    matches = prompt_workflow.find_execution_record_by_id(
        args.project_root, args.execution_id
    )
    if not matches:
        print(
            f"error: no execution record found with execution_id "
            f"{args.execution_id!r}",
            file=sys.stderr,
        )
        return 1
    if len(matches) > 1:
        print(
            f"error: ambiguous -- {len(matches)} execution records share "
            f"execution_id {args.execution_id!r}",
            file=sys.stderr,
        )
        return 2

    try:
        prompt_workflow.write_session_transcript_field(matches[0].path, host_id)
    except prompt_workflow.SessionTranscriptWriteError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"linked: {matches[0].path} -> session_transcript: claude-app:{host_id}")
    return 0


def _run_report(args: argparse.Namespace) -> int:
    try:
        report = prompt_workflow_sessions.build_session_report(
            args.project_root,
            archive_root=args.archive_root,
            since_created_at=args.since_created_at,
        )
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    if args.format == "json":
        print(json.dumps(report.to_json_dict(), indent=2, sort_keys=True))
        return 0
    _print_report_text(report)
    return 0


def _print_report_text(report: prompt_workflow_sessions.SessionReport) -> None:
    print("session archive report")
    print(f"records checked: {report.records_checked}")
    print(f"pointers checked: {report.pointers_checked}")
    print(f"archived pointers: {report.archived}")
    print(f"terminal none pointers: {report.terminal_none}")
    for label, findings in (
        ("pending", report.pending),
        ("dangling", report.dangling),
        ("unarchived", report.unarchived),
        ("unsupported", report.unsupported),
        ("missing", report.missing),
    ):
        print(f"{label}: {len(findings)}")
        for finding in findings:
            pointer = (
                f" session_transcript={finding.session_transcript}"
                if finding.session_transcript
                else ""
            )
            print(
                f"  - {finding.execution_id} [{finding.status}]"
                f"{pointer} :: {finding.reason} ({finding.path})"
            )
