"""Durable private archive helpers for Codex conversation exports."""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import json
import os
import pathlib
import re
import shutil
import sys
import tempfile
import typing

from lrh import prompt_workflow_sessions
from lrh.conversations import (
    codex_app_server_export,
    codex_session,
    export_inspector,
)

ATTEMPT_KIND = "lrh_codex_export_attempt"
ATTEMPT_SCHEMA_VERSION = 1
CODEX_ARCHIVE_SUBDIR = "codex"
EXPORTS_SUBDIR = "exports"
IMPORTS_SUBDIR = "imports"
SCRATCH_WARNING = "scratch_export_ephemeral"
SAFE_COMPONENT_RE = re.compile(r"[^A-Za-z0-9._-]+")
TIMESTAMP_RE = re.compile(r"(\d{8}T\d{6}Z)")


class CodexArchiveError(ValueError):
    """Raised when a durable Codex export archive operation fails."""


@dataclasses.dataclass(frozen=True)
class CodexArchivePaths:
    """Concrete archive paths for one Codex export attempt."""

    directory: pathlib.Path
    export_path: pathlib.Path
    raw_path: pathlib.Path
    attempt_path: pathlib.Path
    ephemeral: bool = False


@dataclasses.dataclass(frozen=True)
class CodexArchiveExportResult:
    """Result of exporting one Codex thread into the private archive."""

    paths: CodexArchivePaths
    export_result: codex_app_server_export.CodexAppServerExport
    inspection: export_inspector.ConversationExportInspection


@dataclasses.dataclass(frozen=True)
class CodexImportResult:
    """Result of importing or classifying one existing Codex export directory."""

    source: pathlib.Path
    destination: pathlib.Path | None
    status: str
    details: tuple[str, ...] = ()


def resolve_codex_archive_root(
    archive_root: str | pathlib.Path | None = None,
) -> pathlib.Path:
    """Resolve the Codex export archive root under the session archive."""

    root = prompt_workflow_sessions.resolve_archive_root(archive_root)
    codex_root = root / CODEX_ARCHIVE_SUBDIR
    _reject_archive_root_inside_current_git_worktree(codex_root)
    return codex_root


def plan_codex_export_paths(
    *,
    thread_id: str,
    archive_root: str | pathlib.Path | None = None,
    exported_at: datetime.datetime | None = None,
    scratch: bool = False,
    scratch_root: str | pathlib.Path | None = None,
) -> CodexArchivePaths:
    """Choose private output paths for one Codex export attempt."""

    timestamp = _timestamp(exported_at)
    safe_thread = _safe_component(thread_id, fallback="unknown-thread")
    directory_name = f"lrh-codex-export-{timestamp}-{safe_thread[:32]}"
    if scratch:
        parent = _scratch_parent(scratch_root)
        directory = pathlib.Path(
            tempfile.mkdtemp(prefix=f"{directory_name}.", dir=str(parent))
        )
        ephemeral = True
    else:
        directory = (
            resolve_codex_archive_root(archive_root)
            / EXPORTS_SUBDIR
            / timestamp[:4]
            / timestamp[4:6]
            / directory_name
        )
        ephemeral = False
    return CodexArchivePaths(
        directory=directory,
        export_path=directory / "export.md",
        raw_path=directory / "raw.json",
        attempt_path=directory / "attempt.json",
        ephemeral=ephemeral,
    )


def archive_codex_thread(
    *,
    thread_id: str,
    archive_root: str | pathlib.Path | None = None,
    scratch: bool = False,
    scratch_root: str | pathlib.Path | None = None,
    codex_command: typing.Sequence[str] | str = "codex",
    timeout_seconds: float = 10.0,
    scan_sensitive: bool = True,
    exported_at: datetime.datetime | None = None,
) -> CodexArchiveExportResult:
    """Export one Codex thread into the durable archive, with attempt metadata."""

    if not thread_id:
        raise CodexArchiveError("thread_id is required")
    resolved_exported_at = _resolved_exported_at(exported_at)
    started_at = _now_iso()
    paths = plan_codex_export_paths(
        thread_id=thread_id,
        archive_root=archive_root,
        exported_at=resolved_exported_at,
        scratch=scratch,
        scratch_root=scratch_root,
    )
    paths = _reserve_export_directory(paths)
    _write_attempt(
        paths.attempt_path,
        {
            "status": "started",
            "operation": "export",
            "started_at": started_at,
            "updated_at": started_at,
            "thread_id": thread_id,
            "source_tool": "codex",
            "source_adapter": codex_app_server_export.SOURCE_ADAPTER,
            "ephemeral": paths.ephemeral,
            "output_paths": _path_mapping(paths),
        },
    )

    try:
        export_result = codex_app_server_export.export_codex_thread(
            thread_id=thread_id,
            output_path=paths.export_path,
            raw_output_path=paths.raw_path,
            codex_command=codex_command,
            scan_sensitive=scan_sensitive,
            timeout_seconds=timeout_seconds,
            exported_at=resolved_exported_at,
        )
        inspection = export_inspector.inspect_export(
            paths.export_path,
            source_path=paths.raw_path,
        )
        status = "succeeded" if inspection.valid else "failed"
        _write_attempt(
            paths.attempt_path,
            {
                "status": status,
                "operation": "export",
                "started_at": started_at,
                "updated_at": _now_iso(),
                "thread_id": thread_id,
                "source_tool": "codex",
                "source_adapter": codex_app_server_export.SOURCE_ADAPTER,
                "ephemeral": paths.ephemeral,
                "output_paths": _path_mapping(paths),
                "source_sha256": export_result.raw_sha256,
                "validation": {
                    "status": "valid" if inspection.valid else "invalid",
                    "errors": list(inspection.errors),
                    "source_hash": inspection.source_hash.status,
                },
            },
        )
    except BaseException as error:
        _write_attempt(
            paths.attempt_path,
            {
                "status": "failed",
                "operation": "export",
                "started_at": started_at,
                "updated_at": _now_iso(),
                "thread_id": thread_id,
                "source_tool": "codex",
                "source_adapter": codex_app_server_export.SOURCE_ADAPTER,
                "ephemeral": paths.ephemeral,
                "output_paths": _path_mapping(paths),
                "error_summary": str(error),
                "files_present": {
                    "export_md": paths.export_path.exists(),
                    "raw_json": paths.raw_path.exists(),
                },
            },
        )
        raise

    if not inspection.valid:
        raise CodexArchiveError(
            f"export verification failed: {', '.join(inspection.errors)}"
        )
    return CodexArchiveExportResult(
        paths=paths,
        export_result=export_result,
        inspection=inspection,
    )


def import_codex_export_directories(
    source_root: pathlib.Path,
    *,
    archive_root: str | pathlib.Path | None = None,
    dry_run: bool = False,
    force: bool = False,
    imported_at: datetime.datetime | None = None,
) -> list[CodexImportResult]:
    """Import existing LRH Codex export directories into the private archive."""

    source = source_root.expanduser()
    if not source.exists():
        raise CodexArchiveError(f"source does not exist: {source}")
    if not source.is_dir():
        raise CodexArchiveError(f"source is not a directory: {source}")
    candidates = _import_candidates(source)
    if not candidates:
        return []
    imported_timestamp = _timestamp(imported_at)
    imported_at_iso = _now_iso()
    results: list[CodexImportResult] = []
    for candidate in candidates:
        results.append(
            _import_one_directory(
                candidate,
                archive_root=archive_root,
                dry_run=dry_run,
                force=force,
                imported_timestamp=imported_timestamp,
                imported_at_iso=imported_at_iso,
            )
        )
    return results


def run_archive_codex_thread_cli(
    argv: typing.Sequence[str] | None = None,
    *,
    prog: str,
) -> int:
    """Run the durable Codex archive export CLI."""

    parser = argparse.ArgumentParser(
        prog=prog,
        description=(
            "Export a Codex thread into LRH's durable private session archive."
        ),
    )
    parser.add_argument(
        "--thread-id",
        default=None,
        help="Codex thread id to export (default: CODEX_THREAD_ID)",
    )
    parser.add_argument(
        "--archive-root",
        default=None,
        help=(
            "session archive root (default: $LRH_SESSION_ARCHIVE_ROOT, else "
            "~/.local/share/lrh/session-archive)"
        ),
    )
    parser.add_argument(
        "--scratch",
        action="store_true",
        help="write to an explicit ephemeral scratch directory instead of the archive",
    )
    parser.add_argument(
        "--scratch-root",
        default=None,
        help="scratch parent directory when --scratch is used",
    )
    parser.add_argument(
        "--codex",
        default=os.environ.get("CODEX", "codex"),
        help="Codex executable path (default: CODEX env var or codex)",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=10.0,
        help="timeout for each app-server response (default: 10)",
    )
    parser.add_argument(
        "--no-scan-sensitive",
        action="store_true",
        help="skip the local heuristic sensitivity scanner",
    )
    args = parser.parse_args(argv)
    try:
        identity = codex_session.resolve_codex_session_identity(args.thread_id)
    except codex_session.CodexSessionIdentityError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    if args.timeout_seconds <= 0:
        print("error: --timeout-seconds must be positive", file=sys.stderr)
        return 2
    if args.scratch_root and not args.scratch:
        print("error: --scratch-root requires --scratch", file=sys.stderr)
        return 2

    try:
        result = archive_codex_thread(
            thread_id=identity.thread_id,
            archive_root=args.archive_root,
            scratch=args.scratch,
            scratch_root=args.scratch_root,
            codex_command=args.codex,
            timeout_seconds=args.timeout_seconds,
            scan_sensitive=not args.no_scan_sensitive,
        )
    except (
        OSError,
        CodexArchiveError,
        codex_app_server_export.CodexAppServerExportError,
    ) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1

    export_result = result.export_result
    paths = result.paths
    if (
        export_result.sensitivity_result is not None
        and export_result.sensitivity_result.findings
    ):
        finding_count = len(export_result.sensitivity_result.findings)
        print(
            "warning: potential sensitive content detected "
            f"by heuristic scanner ({finding_count} finding(s))",
            file=sys.stderr,
        )
    if export_result.stderr_diagnostics:
        print(
            "warning: Codex app-server emitted stderr diagnostics: "
            f"{export_result.stderr_diagnostics}",
            file=sys.stderr,
        )
    print(f"Archived Codex thread: {paths.export_path}")
    print(f"Raw capture: {paths.raw_path}")
    print(f"Attempt metadata: {paths.attempt_path}")
    print(f"Archive directory: {paths.directory}")
    print(f"Ephemeral: {'yes' if paths.ephemeral else 'no'}")
    if paths.ephemeral:
        print(f"Warning: {SCRATCH_WARNING}")
    print("Privacy: private")
    print(f"Sensitivity: {export_result.manifest.sensitivity}")
    print(f"Warnings: {len(export_result.manifest.warnings)}")
    print(f"Turns: {export_result.manifest.transcript_statistics.turn_count}")
    print(f"Messages: {export_result.manifest.transcript_statistics.message_count}")
    print(f"Item types: {_format_item_type_counts(export_result.item_type_counts)}")
    print(f"Source SHA-256: {export_result.raw_sha256}")
    print(f"Validation: {'valid' if result.inspection.valid else 'invalid'}")
    return 0


def run_import_codex_exports_cli(
    argv: typing.Sequence[str] | None = None,
    *,
    prog: str,
) -> int:
    """Run the Codex export import CLI."""

    parser = argparse.ArgumentParser(
        prog=prog,
        description=(
            "Import existing LRH Codex export directories into the durable "
            "private session archive without printing transcript bodies."
        ),
    )
    parser.add_argument("source", help="directory containing Codex export dirs")
    parser.add_argument(
        "--archive-root",
        default=None,
        help=(
            "session archive root (default: $LRH_SESSION_ARCHIVE_ROOT, else "
            "~/.local/share/lrh/session-archive)"
        ),
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace an existing imported directory with the same destination name",
    )
    args = parser.parse_args(argv)

    try:
        results = import_codex_export_directories(
            pathlib.Path(args.source),
            archive_root=args.archive_root,
            dry_run=args.dry_run,
            force=args.force,
        )
    except (OSError, CodexArchiveError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1

    for result in results:
        destination = (
            "(dry-run)" if result.destination is None else str(result.destination)
        )
        detail_text = f" ({'; '.join(result.details)})" if result.details else ""
        print(f"{result.status}: {result.source} -> {destination}{detail_text}")
    status_counts: dict[str, int] = {}
    for result in results:
        status_counts[result.status] = status_counts.get(result.status, 0) + 1
    summary = ", ".join(
        f"{status}={status_counts[status]}" for status in sorted(status_counts)
    )
    print(f"import summary: {summary or 'none'}")
    return 0


def _import_one_directory(
    source: pathlib.Path,
    *,
    archive_root: str | pathlib.Path | None,
    dry_run: bool,
    force: bool,
    imported_timestamp: str,
    imported_at_iso: str,
) -> CodexImportResult:
    export_path = source / "export.md"
    raw_path = source / "raw.json"
    status, details = _classify_source_export(export_path, raw_path)
    dest = _import_destination(
        source,
        archive_root=archive_root,
        status=status,
        imported_timestamp=imported_timestamp,
        export_path=export_path,
    )
    if dry_run:
        return CodexImportResult(
            source=source, destination=None, status=status, details=details
        )
    if dest.exists():
        if not force:
            return CodexImportResult(
                source=source,
                destination=dest,
                status="skipped_existing",
                details=(f"destination exists: {dest}",),
            )
        shutil.rmtree(dest)
    _prepare_private_directory(dest)
    copied_export_path = dest / "export.md"
    copied_raw_path = dest / "raw.json"
    attempt_path = dest / "attempt.json"
    imported_thread_id = _imported_thread_id(export_path, raw_path, status)
    if export_path.exists() and export_path.is_file():
        shutil.copy2(export_path, copied_export_path)
        _chmod_private_file(copied_export_path)
    if raw_path.exists() and raw_path.is_file():
        shutil.copy2(raw_path, copied_raw_path)
        _chmod_private_file(copied_raw_path)
    _write_attempt(
        attempt_path,
        {
            "status": status,
            "operation": "import",
            "started_at": imported_at_iso,
            "updated_at": imported_at_iso,
            "source_tool": "codex",
            "source_adapter": codex_app_server_export.SOURCE_ADAPTER,
            "source_directory": str(source),
            **({"thread_id": imported_thread_id} if imported_thread_id else {}),
            "ephemeral": False,
            "output_paths": {
                "directory": str(dest),
                "export_md": str(copied_export_path),
                "raw_json": str(copied_raw_path),
                "attempt_json": str(attempt_path),
            },
            "validation": {"status": status, "details": list(details)},
        },
    )
    return CodexImportResult(
        source=source,
        destination=dest,
        status=status,
        details=details,
    )


def _imported_thread_id(
    export_path: pathlib.Path,
    raw_path: pathlib.Path,
    status: str,
) -> str | None:
    if status != "imported":
        return None
    try:
        inspection = export_inspector.inspect_export(export_path, source_path=raw_path)
    except export_inspector.ConversationExportInspectionError:
        return None
    if not inspection.valid or inspection.manifest is None:
        return None
    return inspection.manifest.source_id


def _classify_source_export(
    export_path: pathlib.Path,
    raw_path: pathlib.Path,
) -> tuple[str, tuple[str, ...]]:
    export_present = export_path.exists() and export_path.is_file()
    raw_present = raw_path.exists() and raw_path.is_file()
    if not export_present and not raw_present:
        return "empty", ("missing export.md", "missing raw.json")
    if not export_present or not raw_present:
        details = []
        if not export_present:
            details.append("missing export.md")
        if not raw_present:
            details.append("missing raw.json")
        return "partial", tuple(details)
    try:
        inspection = export_inspector.inspect_export(export_path, source_path=raw_path)
    except export_inspector.ConversationExportInspectionError as error:
        return "invalid", (str(error),)
    if inspection.valid:
        return "imported", (
            (
                f"turns={inspection.manifest.transcript_statistics.turn_count}"
                if inspection.manifest is not None
                else "valid"
            ),
        )
    return "invalid", tuple(inspection.errors)


def _import_candidates(source: pathlib.Path) -> list[pathlib.Path]:
    if (source / "export.md").exists() or (source / "raw.json").exists():
        return [source]
    return sorted(path for path in source.iterdir() if path.is_dir())


def _import_destination(
    source: pathlib.Path,
    *,
    archive_root: str | pathlib.Path | None,
    status: str,
    imported_timestamp: str,
    export_path: pathlib.Path,
) -> pathlib.Path:
    timestamp = _timestamp_from_source(source, export_path) or imported_timestamp
    safe_name = _safe_component(source.name, fallback="codex-export")
    return (
        resolve_codex_archive_root(archive_root)
        / IMPORTS_SUBDIR
        / timestamp[:4]
        / timestamp[4:6]
        / f"{safe_name}-{status}"
    )


def _timestamp_from_source(
    source: pathlib.Path,
    export_path: pathlib.Path,
) -> str | None:
    match = TIMESTAMP_RE.search(source.name)
    if match:
        return match.group(1)
    if export_path.exists() and export_path.is_file():
        try:
            inspection = export_inspector.inspect_export(export_path)
        except export_inspector.ConversationExportInspectionError:
            return None
        if inspection.manifest is not None:
            return _timestamp_from_iso(inspection.manifest.exported_at)
    return None


def _timestamp_from_iso(value: str) -> str | None:
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return _timestamp(parsed)


def _prepare_private_directory(path: pathlib.Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    try:
        path.chmod(0o700)
    except OSError:
        pass


def _reserve_export_directory(paths: CodexArchivePaths) -> CodexArchivePaths:
    if paths.ephemeral:
        _chmod_private_directory(paths.directory)
        return paths

    parent = paths.directory.parent
    parent.mkdir(parents=True, exist_ok=True)
    for index in range(1, 1000):
        directory = (
            paths.directory
            if index == 1
            else paths.directory.with_name(f"{paths.directory.name}-{index}")
        )
        try:
            directory.mkdir(mode=0o700)
        except FileExistsError:
            continue
        _chmod_private_directory(directory)
        return CodexArchivePaths(
            directory=directory,
            export_path=directory / paths.export_path.name,
            raw_path=directory / paths.raw_path.name,
            attempt_path=directory / paths.attempt_path.name,
            ephemeral=paths.ephemeral,
        )
    raise CodexArchiveError(
        f"could not allocate unique export directory: {paths.directory}"
    )


def _chmod_private_directory(path: pathlib.Path) -> None:
    try:
        path.chmod(0o700)
    except OSError:
        pass


def _reject_archive_root_inside_current_git_worktree(path: pathlib.Path) -> None:
    git_root = _current_git_worktree_root()
    if git_root is None:
        return
    try:
        archive_path = path.resolve(strict=False)
    except OSError:
        archive_path = path.absolute()
    if archive_path == git_root or git_root in archive_path.parents:
        raise CodexArchiveError("archive root must be outside the current Git worktree")


def _current_git_worktree_root() -> pathlib.Path | None:
    try:
        current = pathlib.Path.cwd().resolve(strict=False)
    except OSError:
        current = pathlib.Path.cwd().absolute()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def _write_attempt(path: pathlib.Path, fields: dict[str, typing.Any]) -> None:
    payload = {
        "kind": ATTEMPT_KIND,
        "schema_version": ATTEMPT_SCHEMA_VERSION,
        **fields,
    }
    content = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(tmp_name, path)
        _chmod_private_file(path)
    except BaseException:
        try:
            os.remove(tmp_name)
        except FileNotFoundError:
            pass
        raise


def _chmod_private_file(path: pathlib.Path) -> None:
    try:
        path.chmod(0o600)
    except OSError:
        pass


def _path_mapping(paths: CodexArchivePaths) -> dict[str, str]:
    return {
        "directory": str(paths.directory),
        "export_md": str(paths.export_path),
        "raw_json": str(paths.raw_path),
        "attempt_json": str(paths.attempt_path),
    }


def _format_item_type_counts(item_type_counts: typing.Mapping[str, int]) -> str:
    if not item_type_counts:
        return "(none)"
    return ", ".join(
        f"{item_type}={item_type_counts[item_type]}"
        for item_type in sorted(item_type_counts)
    )


def _scratch_parent(scratch_root: str | pathlib.Path | None) -> pathlib.Path:
    parent = (
        pathlib.Path(scratch_root).expanduser()
        if scratch_root
        else pathlib.Path(os.environ.get("TMPDIR") or tempfile.gettempdir())
    )
    parent.mkdir(parents=True, exist_ok=True)
    return parent


def _timestamp(value: datetime.datetime | None = None) -> str:
    timestamp = value or datetime.datetime.now(datetime.timezone.utc)
    if timestamp.tzinfo is None:
        raise CodexArchiveError("timestamp must be timezone-aware")
    return timestamp.astimezone(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _resolved_exported_at(
    value: datetime.datetime | None = None,
) -> datetime.datetime:
    timestamp = value or datetime.datetime.now(datetime.timezone.utc)
    if timestamp.tzinfo is None:
        raise CodexArchiveError("timestamp must be timezone-aware")
    return timestamp


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _safe_component(value: str, *, fallback: str) -> str:
    cleaned = SAFE_COMPONENT_RE.sub("-", value.strip()).strip(".-")
    return cleaned or fallback
