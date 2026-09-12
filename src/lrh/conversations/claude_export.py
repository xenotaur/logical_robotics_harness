"""Convert local Claude Code session transcripts to Markdown export artifacts."""

from __future__ import annotations

import argparse
import dataclasses
import glob
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence

from lrh import prompt_workflow_sessions
from lrh.conversations import export_manifest, sensitivity

DEFAULT_ADAPTER_NAME = "claude_transcript_jsonl"
ADAPTER_VERSION = 1
CLAUDE_ARCHIVE_SUBDIR = "claude"
EXPORTS_SUBDIR = "exports"


class ClaudeExportError(ValueError):
    """Raised when a Claude Code transcript export fails."""


@dataclasses.dataclass(frozen=True)
class ClaudeExport:
    """Result of converting a Claude Code JSONL session transcript to Markdown."""

    markdown: str
    manifest: export_manifest.ConversationExportManifest
    sensitivity_result: sensitivity.SensitiveScanResult | None


def convert_claude_session(
    transcript_path: Path,
    *,
    output_path: Path | None = None,
    force: bool = False,
    scan_sensitive: bool = True,
    source_id: str | None = None,
    exported_at: str | None = None,
    include_system_attachments: bool = False,
    include_subagents: bool = False,
) -> ClaudeExport:
    """Convert a Claude Code session JSONL transcript into a private Markdown export."""

    path = _expand_user_path(transcript_path, description="transcript path")
    if not path.exists():
        raise ClaudeExportError(f"transcript file does not exist: {path}")
    if not path.is_file():
        raise ClaudeExportError(f"transcript path is not a file: {path}")

    try:
        raw_bytes = path.read_bytes()
    except OSError as err:
        raise ClaudeExportError(f"could not read transcript file: {path}") from err

    source_sha256 = hashlib.sha256(raw_bytes).hexdigest()

    try:
        raw_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as err:
        raise ClaudeExportError(f"transcript file is not valid UTF-8: {path}") from err

    steps, warnings = _parse_jsonl_lines(raw_text)
    if not steps and not warnings:
        warnings.append("transcript file contains no valid step objects")

    subagents = _find_subagent_transcripts(path)

    rendered_body, subagent_warnings = _render_claude_transcript(
        steps,
        include_system_attachments=include_system_attachments,
        subagents=subagents,
        include_subagents=include_subagents,
    )
    warnings.extend(subagent_warnings)
    body = rendered_body if rendered_body.endswith("\n") else f"{rendered_body}\n"

    scan_res: sensitivity.SensitiveScanResult | None = None
    if scan_sensitive:
        scan_res = sensitivity.scan_text_for_sensitive_findings(body)
        sensitivity_status = (
            export_manifest.SENSITIVITY_POTENTIAL
            if scan_res.status == sensitivity.STATUS_POTENTIAL
            else export_manifest.SENSITIVITY_NONE_DETECTED
        )
        scan_metadata: dict[str, object] = {
            "status": export_manifest.SCAN_STATUS_SCANNED,
            "scanner": "lrh.conversations.sensitivity",
            "scanner_version": "1.0",
            "finding_count": scan_res.finding_count,
            "categories": list(scan_res.categories),
        }
    else:
        sensitivity_status = export_manifest.SENSITIVITY_UNSCANNED
        scan_metadata = {"status": export_manifest.SCAN_STATUS_NOT_SCANNED}

    now_iso = (
        datetime.now(timezone.utc).isoformat() if exported_at is None else exported_at
    )

    stats = export_manifest.statistics_for_text(
        body,
        turn_count=_count_turns(steps),
        message_count=_count_messages(steps),
    )

    manifest_obj = export_manifest.ConversationExportManifest(
        source_sha256=source_sha256,
        exported_at=now_iso,
        transcript_statistics=stats,
        sensitivity_scan=scan_metadata,
        kind=export_manifest.KIND_CLAUDE,
        schema_version=export_manifest.SCHEMA_VERSION,
        source_tool=export_manifest.SOURCE_TOOL_CLAUDE_CODE,
        source_adapter=DEFAULT_ADAPTER_NAME,
        privacy=export_manifest.DEFAULT_PRIVACY,
        authority=export_manifest.DEFAULT_AUTHORITY,
        sensitivity=sensitivity_status,
        source_id=source_id or _derive_source_id(path, source_sha256=source_sha256),
        adapter_version=ADAPTER_VERSION,
        warnings=tuple(warnings),
    )

    full_markdown = f"{manifest_obj.to_frontmatter()}\n{body}"

    if output_path is not None:
        out = _expand_user_path(output_path, description="output path")
        _reject_source_output_collision(path, out)
        if out.exists() and not force:
            raise FileExistsError(f"output path already exists: {out}")
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            _write_private_text(out, full_markdown)
        except OSError as err:
            raise ClaudeExportError(
                f"could not write output export file: {out}"
            ) from err

    return ClaudeExport(
        markdown=full_markdown,
        manifest=manifest_obj,
        sensitivity_result=scan_res,
    )


def _write_private_text(path: Path, content: str) -> None:
    """Write text to path with user-only (0600) permissions from creation.

    Writing via ``Path.write_text`` and chmod-ing afterward leaves a window,
    under a permissive umask (e.g. 022), where the file is briefly created
    with broader default permissions before the chmod call narrows them —
    and if the chmod call itself silently fails, that exposure is permanent.
    Passing an explicit 0o600 mode to ``os.open`` avoids the window: POSIX
    applies ``mode & ~umask``, and no typical umask can widen 0o600's
    already-owner-only bits, so the file is never observably more open than
    0o600 at any point after creation.
    """
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        fchmod = getattr(os, "fchmod", None)
        if fchmod is not None:
            try:
                fchmod(handle.fileno(), 0o600)
            except OSError:
                pass
        handle.write(content)


def _reject_source_output_collision(source: Path, destination: Path) -> None:
    if destination.exists():
        try:
            if source.samefile(destination):
                raise ClaudeExportError(
                    "transcript source and output path must refer to different files"
                )
        except OSError:
            pass
    try:
        same_path = source.resolve(strict=True) == destination.resolve(strict=False)
    except OSError:
        same_path = source.absolute() == destination.absolute()
    if same_path:
        raise ClaudeExportError(
            "transcript source and output path must refer to different files"
        )


def _expand_user_path(path: Path, *, description: str) -> Path:
    """Expand ``~`` in a path, converting an unresolvable-home failure into
    a clean ``ClaudeExportError`` instead of an unhandled ``RuntimeError``.

    ``Path.expanduser()`` raises ``RuntimeError`` when the home directory
    for a named user (e.g. ``~missing-user/export.md``) cannot be resolved
    on the current platform — that failure otherwise surfaces as a raw
    Python traceback instead of this module's documented concise error.
    """
    try:
        return path.expanduser()
    except RuntimeError as err:
        raise ClaudeExportError(f"could not resolve {description}: {err}") from err


def resolve_claude_archive_root(archive_root: str | Path | None = None) -> Path:
    """Resolve the Claude export archive root under the session archive."""
    root = prompt_workflow_sessions.resolve_archive_root(archive_root)
    claude_root = root / CLAUDE_ARCHIVE_SUBDIR
    _reject_archive_root_inside_current_git_worktree(claude_root)
    return claude_root


def _reject_archive_root_inside_current_git_worktree(path: Path) -> None:
    git_root = _current_git_worktree_root()
    if git_root is None:
        return
    try:
        archive_path = path.resolve(strict=False)
    except OSError:
        archive_path = path.absolute()
    if archive_path == git_root or git_root in archive_path.parents:
        raise ClaudeExportError("archive root must be outside the current Git worktree")


def _current_git_worktree_root() -> Path | None:
    try:
        current = Path.cwd().resolve(strict=False)
    except OSError:
        current = Path.cwd().absolute()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def _derive_source_id(path: Path, source_sha256: str | None = None) -> str:
    """Derive a session identifier from the transcript filename."""
    stem = path.stem
    if stem:
        return stem
    if source_sha256:
        return source_sha256[:12]
    return "unknown-session"


def _resolve_transcript_path(
    *,
    transcript_path: str | None,
    session_id: str | None,
    app_data_dir: Path,
    latest: bool,
) -> Path:
    """Resolve a Claude Code transcript path by explicit path, session id, or latest."""

    if transcript_path:
        return _expand_user_path(Path(transcript_path), description="transcript path")

    app_dir = _expand_user_path(app_data_dir, description="app data directory")
    projects_dir = app_dir / "projects"

    if session_id:
        sid = session_id.strip()
        if not sid or "/" in sid or "\\" in sid:
            raise ClaudeExportError(f"invalid session id: {session_id!r}")
        matches = sorted(projects_dir.glob(f"*/{glob.escape(sid)}.jsonl"))
        if not matches:
            raise ClaudeExportError(
                f"no transcript file found for session id '{sid}' under {projects_dir}"
            )
        if len(matches) > 1:
            raise ClaudeExportError(
                f"multiple transcript files found for session id '{sid}' under "
                f"{projects_dir}; disambiguate with an explicit transcript path: "
                + ", ".join(str(match) for match in matches)
            )
        return matches[0]

    if latest:
        if not projects_dir.exists():
            raise ClaudeExportError(
                f"Claude projects directory does not exist: {projects_dir}"
            )
        matches = list(projects_dir.glob("*/*.jsonl"))
        if not matches:
            raise ClaudeExportError(
                f"no Claude session transcript files found in {projects_dir}"
            )
        matches.sort(key=lambda candidate: candidate.stat().st_mtime, reverse=True)
        return matches[0]

    raise ClaudeExportError("one of transcript_path, session_id, or latest is required")


def _default_app_data_dir() -> str:
    """Return the default Claude Code application data directory.

    Honors ``CLAUDE_CONFIG_DIR`` (Claude Code's own override for relocating
    session storage off ``~/.claude``) the same way the CLI documentation
    describes; falls back to ``~/.claude`` when unset.
    """
    return os.environ.get("CLAUDE_CONFIG_DIR") or "~/.claude"


def run_convert_claude_session_cli(
    argv: Sequence[str] | None = None,
    *,
    prog: str | None = None,
) -> int:
    """CLI entry point for converting Claude Code session transcripts."""
    parser = argparse.ArgumentParser(
        prog=prog or "lrh conversation export-claude-session",
        description=(
            "Convert a local Claude Code session transcript log (JSONL) into "
            "a private, non-authoritative Markdown export artifact."
        ),
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--transcript-path",
        help="explicit path to a Claude Code session transcript JSONL file",
    )
    input_group.add_argument(
        "--session-id",
        help="Claude Code session id to discover under app-data-dir/projects/*/",
    )
    input_group.add_argument(
        "--latest",
        action="store_true",
        help="discover the most recently modified transcript file under app-data-dir",
    )
    parser.add_argument(
        "--app-data-dir",
        default=_default_app_data_dir(),
        help=(
            "path to Claude Code's application data directory "
            "(default: $CLAUDE_CONFIG_DIR, or ~/.claude if unset)"
        ),
    )
    parser.add_argument(
        "--out",
        required=False,
        default=None,
        help="Markdown export output path (default: durable session archive)",
    )
    parser.add_argument(
        "--archive-root",
        help="optional private session archive root override",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite existing output file if present",
    )
    parser.add_argument(
        "--source-id",
        help="optional explicit session id to record in metadata",
    )
    parser.add_argument(
        "--no-scan-sensitive",
        action="store_true",
        help="skip heuristic sensitive content scanner",
    )
    parser.add_argument(
        "--include-system-attachments",
        action="store_true",
        help="include internal system-context attachment records in the export",
    )
    parser.add_argument(
        "--include-subagents",
        action="store_true",
        help="inline full subagent transcripts instead of only referencing them",
    )

    args = parser.parse_args(argv)

    try:
        transcript_file = _resolve_transcript_path(
            transcript_path=args.transcript_path,
            session_id=args.session_id,
            app_data_dir=Path(args.app_data_dir),
            latest=args.latest,
        )
    except (ClaudeExportError, OSError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1

    if args.out:
        try:
            output_path = _expand_user_path(Path(args.out), description="--out path")
        except ClaudeExportError as err:
            print(f"error: {err}", file=sys.stderr)
            return 1
    else:
        try:
            archive_root = resolve_claude_archive_root(args.archive_root)
        except (ClaudeExportError, OSError) as err:
            print(f"error: {err}", file=sys.stderr)
            return 1
        now_utc = datetime.now(timezone.utc)
        year = now_utc.strftime("%Y")
        month = now_utc.strftime("%m")
        try:
            raw_bytes = transcript_file.read_bytes()
            sha = hashlib.sha256(raw_bytes).hexdigest()
        except OSError:
            sha = None
        sid = args.source_id or _derive_source_id(transcript_file, source_sha256=sha)
        safe_sid = "".join(c if c.isalnum() or c in "-_" else "_" for c in sid)
        output_path = archive_root / EXPORTS_SUBDIR / year / month / f"{safe_sid}.md"

    try:
        result = convert_claude_session(
            transcript_file,
            output_path=output_path,
            force=args.force,
            scan_sensitive=not args.no_scan_sensitive,
            source_id=args.source_id,
            include_system_attachments=args.include_system_attachments,
            include_subagents=args.include_subagents,
        )
    except (ClaudeExportError, FileExistsError, OSError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1

    if result.sensitivity_result is not None and result.sensitivity_result.findings:
        finding_count = len(result.sensitivity_result.findings)
        print(
            "warning: potential sensitive content detected "
            f"({finding_count} finding(s))",
            file=sys.stderr,
        )

    out_display = str(output_path) if output_path else "(memory only)"
    print(f"Exported Claude Code session transcript: {out_display}")
    print(f"Source ID: {result.manifest.source_id or 'unknown'}")
    print(f"Source SHA-256: {result.manifest.source_sha256}")
    print(f"Privacy: {result.manifest.privacy}")
    print(f"Sensitivity: {result.manifest.sensitivity}")
    print(f"Warnings: {len(result.manifest.warnings)}")
    return 0


def _find_subagent_transcripts(transcript_path: Path) -> list[tuple[Path, dict]]:
    """Find sibling subagent transcripts for a session, with their metadata."""

    subagents_dir = transcript_path.parent / transcript_path.stem / "subagents"
    if not subagents_dir.is_dir():
        return []

    results: list[tuple[Path, dict]] = []
    for jsonl_file in sorted(subagents_dir.glob("agent-*.jsonl")):
        meta_file = jsonl_file.with_suffix(".meta.json")
        meta: dict = {}
        if meta_file.exists():
            try:
                loaded = json.loads(meta_file.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    meta = loaded
            except (OSError, json.JSONDecodeError):
                meta = {}
        results.append((jsonl_file, meta))
    return results


def _parse_jsonl_lines(raw_text: str) -> tuple[list[dict], list[str]]:
    """Parse JSONL text into step objects, collecting per-line warnings."""

    steps: list[dict] = []
    warnings: list[str] = []
    for index, line in enumerate(raw_text.splitlines(), start=1):
        line_str = line.strip()
        if not line_str:
            continue
        try:
            parsed = json.loads(line_str)
        except json.JSONDecodeError as err:
            warnings.append(f"line {index}: invalid JSON: {err}")
            continue
        if isinstance(parsed, dict):
            steps.append(parsed)
        else:
            warnings.append(f"line {index}: JSON item is not an object")
    return steps, warnings


def _load_jsonl_steps(path: Path) -> tuple[list[dict], list[str]]:
    """Load step objects and filename-qualified warnings from a subagent transcript."""

    try:
        raw_text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as err:
        return [], [f"{path.name}: could not read subagent transcript: {err}"]
    steps, warnings = _parse_jsonl_lines(raw_text)
    return steps, [f"{path.name}: {warning}" for warning in warnings]


def _is_genuine_human_turn(step: Mapping[str, object]) -> bool:
    """Return True if a type=="user" step carries human-authored content.

    A tool_result reply is also delivered as a type=="user" record, with
    message.content a list containing a {"type": "tool_result", ...} block
    rather than actual human-typed text. Such records are not human turns.
    """
    message = step.get("message")
    if not isinstance(message, Mapping):
        return False
    content = message.get("content")
    if isinstance(content, str):
        return True
    if isinstance(content, list):
        return any(
            not (isinstance(block, Mapping) and block.get("type") == "tool_result")
            for block in content
        )
    return False


def _count_turns(steps: Sequence[Mapping[str, object]]) -> int:
    """Count genuine human user turns in step payload."""
    return sum(
        1
        for step in steps
        if step.get("type") == "user"
        and "message" in step
        and _is_genuine_human_turn(step)
    )


def _count_messages(steps: Sequence[Mapping[str, object]]) -> int:
    """Count user and assistant message steps."""
    return sum(
        1
        for step in steps
        if step.get("type") in ("user", "assistant") and "message" in step
    )


def _render_claude_transcript(
    steps: Sequence[Mapping[str, object]],
    *,
    include_system_attachments: bool,
    subagents: Sequence[tuple[Path, dict]],
    include_subagents: bool,
) -> tuple[str, list[str]]:
    """Render Claude Code JSONL step objects into readable Markdown.

    Returns the rendered Markdown body and any filename-qualified warnings
    collected while loading inlined subagent transcripts (only populated
    when ``include_subagents`` is True; referenced-only subagents are never
    parsed, so they never contribute warnings).
    """

    title: str | None = None
    for step in steps:
        if step.get("type") == "ai-title":
            candidate = step.get("aiTitle")
            if isinstance(candidate, str) and candidate.strip():
                title = candidate.strip()

    lines: list[str] = [
        f"# {title}" if title else "# Claude Code Session Transcript",
        "",
    ]
    subagent_warnings: list[str] = []

    for step in steps:
        step_type = step.get("type")

        if step_type in ("queue-operation", "ai-title"):
            continue

        if step_type == "attachment":
            if include_system_attachments:
                lines.extend(_render_attachment(step))
            continue

        if step_type == "user":
            lines.extend(_render_message_block("User", step))
        elif step_type == "assistant":
            lines.extend(_render_message_block("Assistant", step))
        # Unknown/unrecognized record types are silently skipped for
        # forward compatibility with an internal, versioned JSONL format.

    if subagents:
        lines.append("## Subagents")
        lines.append("")
        for jsonl_file, meta in subagents:
            agent_id = jsonl_file.stem
            agent_type = meta.get("agentType")
            description = meta.get("description")
            detail = " ".join(
                part
                for part in (
                    f"({agent_type})" if agent_type else None,
                    description if isinstance(description, str) else None,
                )
                if part
            )
            entry = f"- **{agent_id}**"
            if detail:
                entry = f"{entry} {detail}"
            lines.append(entry)
        lines.append("")

        if include_subagents:
            for jsonl_file, _meta in subagents:
                lines.append(f"### Subagent transcript: {jsonl_file.stem}")
                lines.append("")
                sub_steps, sub_load_warnings = _load_jsonl_steps(jsonl_file)
                subagent_warnings.extend(sub_load_warnings)
                sub_body, sub_render_warnings = _render_claude_transcript(
                    sub_steps,
                    include_system_attachments=include_system_attachments,
                    subagents=(),
                    include_subagents=False,
                )
                subagent_warnings.extend(sub_render_warnings)
                # Drop the sub-transcript's own top-level heading; it is
                # nested under this "### Subagent transcript" heading instead.
                sub_lines = sub_body.splitlines()
                if sub_lines and sub_lines[0].startswith("# "):
                    sub_lines = sub_lines[1:]
                lines.extend(line for line in sub_lines)
                lines.append("")

    while lines and lines[-1] == "":
        lines.pop()

    return "\n".join(lines), subagent_warnings


def _render_message_block(role_label: str, step: Mapping[str, object]) -> list[str]:
    message = step.get("message")
    if not isinstance(message, Mapping):
        return []
    body_lines = _render_content_blocks(message.get("content"))
    if not body_lines:
        return []
    return [f"## {role_label}", ""] + body_lines + [""]


def _render_content_blocks(content: object) -> list[str]:
    if isinstance(content, str):
        text = content.strip()
        return [text] if text else []
    if not isinstance(content, list):
        return []

    lines: list[str] = []
    for block in content:
        if not isinstance(block, Mapping):
            continue
        block_type = block.get("type")

        if block_type == "text":
            text = block.get("text")
            if isinstance(text, str) and text.strip():
                lines.append(text.strip())
                lines.append("")

        elif block_type == "thinking":
            thinking = block.get("thinking")
            if isinstance(thinking, str) and thinking.strip():
                lines.append("> **Thinking**")
                for tline in thinking.strip().splitlines():
                    lines.append(f"> {tline}")
                lines.append("")

        elif block_type == "tool_use":
            name = block.get("name", "tool")
            tool_input = block.get("input")
            lines.append(f"### Tool Call: `{name}`")
            lines.append("")
            if tool_input:
                lines.extend(
                    _fenced_code_block(
                        json.dumps(tool_input, indent=2, default=str), language="json"
                    )
                )
                lines.append("")

        elif block_type == "tool_result":
            result_text = _render_tool_result_content(block.get("content"))
            is_error = bool(block.get("is_error"))
            label = "Tool Result (error)" if is_error else "Tool Result"
            lines.append(f"### {label}")
            lines.append("")
            lines.extend(_fenced_code_block(result_text))
            lines.append("")
        # Unknown block types are silently skipped.

    while lines and lines[-1] == "":
        lines.pop()
    return lines


def _fenced_code_block(content: str, *, language: str = "") -> list[str]:
    """Wrap content in a Markdown code fence long enough not to be closed early.

    A fixed triple-backtick fence can be closed prematurely by a backtick run
    already present in the content (e.g. a command's own Markdown output).
    Using a fence one backtick longer than the longest run in the content
    guarantees the fence cannot collide with it.
    """
    longest_run = 0
    current_run = 0
    for char in content:
        if char == "`":
            current_run += 1
            longest_run = max(longest_run, current_run)
        else:
            current_run = 0
    fence = "`" * max(3, longest_run + 1)
    return [f"{fence}{language}", content, fence]


def _render_tool_result_content(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, Mapping) and item.get("type") == "text":
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
    return json.dumps(content, default=str)


def _render_attachment(step: Mapping[str, object]) -> list[str]:
    attachment = step.get("attachment")
    attachment_type = (
        attachment.get("type") if isinstance(attachment, Mapping) else "unknown"
    )
    return [
        f"### System Attachment ({attachment_type})",
        "",
        *_fenced_code_block(
            json.dumps(attachment, indent=2, default=str), language="json"
        ),
        "",
    ]
