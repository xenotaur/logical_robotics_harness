"""Codex app-server conversation export adapter."""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import selectors
import subprocess
import sys
import tempfile
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from lrh.conversations import codex_session, export_manifest, sensitivity

SOURCE_ADAPTER = "codex_app_server_thread_read"
ADAPTER_VERSION = 1
CAPTURE_KIND = "lrh_codex_app_server_thread_read_capture"
CAPTURE_SCHEMA_VERSION = 1
SENSITIVE_CONTENT_WARNING = "potential_sensitive_content_detected"
PRIVATE_RAW_WARNING = "private_raw_transcript_do_not_commit"
REASONING_OMITTED_WARNING = "reasoning_items_omitted"
FILE_CHANGE_METADATA_WARNING = "file_change_metadata_only"
WEB_SEARCH_METADATA_WARNING = "web_search_metadata_only"
CONTEXT_COMPACTION_WARNING = "context_compaction_present"
TRUST_STATE_UNVERIFIED_WARNING = "codex_trust_state_unverified"
APP_SERVER_STDERR_WARNING = "codex_app_server_stderr_diagnostics"
UNKNOWN_ITEM_WARNING_PREFIX = "unknown_item_type"
NON_COMPLETED_TURN_WARNING_PREFIX = "turn_status"
MAX_STDERR_DIAGNOSTIC_BYTES = 4096


class CodexAppServerExportError(ValueError):
    """Raised when a Codex app-server export cannot be completed."""


@dataclasses.dataclass(frozen=True)
class CodexAppServerExport:
    """Markdown export and private raw capture produced from a Codex thread."""

    markdown: str
    raw_capture: Mapping[str, object]
    raw_sha256: str
    manifest: export_manifest.ConversationExportManifest
    sensitivity_result: sensitivity.SensitiveScanResult | None
    rendered_warnings: tuple[str, ...]
    item_type_counts: Mapping[str, int]
    stderr_diagnostics: str | None


@dataclasses.dataclass(frozen=True)
class RenderedThread:
    """Rendered transcript text and renderer metadata."""

    markdown_body: str
    warnings: tuple[str, ...]
    turn_count: int
    message_count: int
    item_type_counts: Mapping[str, int]


@dataclasses.dataclass(frozen=True)
class AppServerThreadRead:
    """Raw app-server thread/read response and bounded diagnostics."""

    response: Mapping[str, object]
    stderr_diagnostics: str | None


class JsonLineReader:
    """Read JSONL from app-server stdout without TextIOWrapper buffering traps."""

    def __init__(self, proc: subprocess.Popen[bytes]) -> None:
        if proc.stdout is None:
            raise CodexAppServerExportError("app-server stdout pipe was not created")
        self._stdout = proc.stdout
        self._selector = selectors.DefaultSelector()
        self._selector.register(self._stdout, selectors.EVENT_READ)
        self._buffer = bytearray()

    def close(self) -> None:
        self._selector.close()

    def read_json_line(
        self,
        proc: subprocess.Popen[bytes],
        *,
        deadline: float,
    ) -> dict[str, Any]:
        """Read one JSON line before the deadline."""

        while True:
            newline_index = self._buffer.find(b"\n")
            if newline_index >= 0:
                raw_line = bytes(self._buffer[:newline_index])
                del self._buffer[: newline_index + 1]
                try:
                    line = raw_line.decode("utf-8").strip()
                except UnicodeDecodeError as err:
                    raise CodexAppServerExportError(
                        "app-server emitted non-UTF-8 output"
                    ) from err
                if not line:
                    continue
                try:
                    loaded = json.loads(line)
                except json.JSONDecodeError as err:
                    raise CodexAppServerExportError(
                        "app-server emitted malformed JSON"
                    ) from err
                if not isinstance(loaded, dict):
                    raise CodexAppServerExportError(
                        "app-server response must be a JSON object"
                    )
                return loaded

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise CodexAppServerExportError(
                    "timed out waiting for app-server response"
                )

            events = self._selector.select(timeout=min(remaining, 0.25))
            if not events:
                if proc.poll() is not None:
                    raise CodexAppServerExportError(
                        f"app-server exited before response: {proc.returncode}"
                    )
                continue

            try:
                chunk = os.read(self._stdout.fileno(), 65536)
            except OSError as err:
                raise CodexAppServerExportError(
                    "could not read app-server stdout"
                ) from err
            if chunk:
                self._buffer.extend(chunk)
            elif proc.poll() is not None:
                raise CodexAppServerExportError(
                    f"app-server exited before response: {proc.returncode}"
                )


def export_codex_thread(
    *,
    thread_id: str,
    output_path: Path,
    raw_output_path: Path,
    codex_command: Sequence[str] | str = "codex",
    force: bool = False,
    scan_sensitive: bool = True,
    timeout_seconds: float = 10.0,
    exported_at: datetime | str | None = None,
) -> CodexAppServerExport:
    """Export a Codex thread through app-server `thread/read`."""

    normalized_thread_id = _normalized_non_empty(thread_id, "thread_id")
    destination = output_path.expanduser()
    raw_destination = raw_output_path.expanduser()
    _reject_output_collision(destination, raw_destination)
    _reject_unsafe_raw_output_path(raw_output_path, raw_destination)
    _reject_existing_output(destination, force)
    _reject_existing_output(raw_destination, force)

    captured_at = _exported_at_value(exported_at)
    request_params = {"threadId": normalized_thread_id, "includeTurns": True}
    read_result = read_thread_from_app_server(
        codex_command=codex_command,
        params=request_params,
        timeout_seconds=timeout_seconds,
    )
    response = read_result.response
    thread = _thread_from_response(response)
    rendered = render_thread(thread)
    raw_capture, raw_bytes, raw_sha256 = build_raw_capture(
        codex_command=codex_command,
        method="thread/read",
        params=request_params,
        response=response,
        captured_at=captured_at,
    )

    scan_result = (
        sensitivity.scan_text_for_sensitive_findings(rendered.markdown_body)
        if scan_sensitive
        else None
    )
    manifest = build_app_server_manifest(
        transcript_text=rendered.markdown_body,
        raw_sha256=raw_sha256,
        thread_id=normalized_thread_id,
        rendered=rendered,
        scan_result=scan_result,
        exported_at=captured_at,
        app_server_warnings=(
            (APP_SERVER_STDERR_WARNING,) if read_result.stderr_diagnostics else ()
        ),
    )
    markdown = render_export_markdown(rendered.markdown_body, manifest)

    _write_private_bytes(raw_destination, raw_bytes)
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(markdown.encode("utf-8"))
    except OSError as err:
        raise CodexAppServerExportError(
            f"Could not write output: {destination}"
        ) from err

    return CodexAppServerExport(
        markdown=markdown,
        raw_capture=raw_capture,
        raw_sha256=raw_sha256,
        manifest=manifest,
        sensitivity_result=scan_result,
        rendered_warnings=rendered.warnings,
        item_type_counts=rendered.item_type_counts,
        stderr_diagnostics=read_result.stderr_diagnostics,
    )


def read_thread_from_app_server(
    *,
    codex_command: Sequence[str] | str,
    params: Mapping[str, object],
    timeout_seconds: float,
) -> AppServerThreadRead:
    """Run the Codex app-server handshake and return a thread/read response."""

    command = _codex_app_server_command(codex_command)
    try:
        stderr_file = tempfile.TemporaryFile()
        try:
            proc = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=stderr_file,
                bufsize=0,
            )
        except OSError:
            stderr_file.close()
            raise
    except OSError as err:
        raise CodexAppServerExportError(
            f"could not start Codex app-server: {command[0]}"
        ) from err

    reader = JsonLineReader(proc)
    response: dict[str, Any] | None = None
    caught_error: CodexAppServerExportError | None = None
    try:
        initialize = {
            "method": "initialize",
            "id": 0,
            "params": {
                "clientInfo": {
                    "name": "lrh_codex_export",
                    "title": "LRH Codex Export",
                    "version": "1.0.0",
                },
                "capabilities": {"experimentalApi": True},
            },
        }
        init_response = _send_request(
            proc,
            reader,
            request=initialize,
            timeout_seconds=timeout_seconds,
        )
        _raise_for_json_rpc_error(init_response, stage="initialize")

        _send_notification(proc, {"method": "initialized", "params": {}})
        response = _send_request(
            proc,
            reader,
            request={"method": "thread/read", "id": 1, "params": dict(params)},
            timeout_seconds=timeout_seconds,
        )
        _raise_for_json_rpc_error(response, stage="thread/read")
    except CodexAppServerExportError as err:
        caught_error = err
    finally:
        reader.close()
        _terminate_process(proc)
        stderr_diagnostics = _read_stderr_diagnostics(stderr_file)
        stderr_file.close()

    if caught_error is not None:
        if stderr_diagnostics:
            raise CodexAppServerExportError(
                f"{caught_error}; app-server stderr: {stderr_diagnostics}"
            ) from caught_error
        raise caught_error

    if response is None:
        raise CodexAppServerExportError("thread/read response was not captured")
    return AppServerThreadRead(
        response=response,
        stderr_diagnostics=stderr_diagnostics,
    )


def build_raw_capture(
    *,
    codex_command: Sequence[str] | str,
    method: str,
    params: Mapping[str, object],
    response: Mapping[str, object],
    captured_at: str,
) -> tuple[dict[str, object], bytes, str]:
    """Build deterministic private raw capture JSON and its SHA-256 digest."""

    envelope: dict[str, object] = {
        "capture_kind": CAPTURE_KIND,
        "capture_schema_version": CAPTURE_SCHEMA_VERSION,
        "captured_at": captured_at,
        "source_command": " ".join(_codex_app_server_command(codex_command)),
        "app_server_method": method,
        "request": dict(params),
        "response_shape": "json_rpc_response_envelope",
        "response": dict(response),
        "capture_warnings": [PRIVATE_RAW_WARNING],
    }
    raw_bytes = (json.dumps(envelope, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return envelope, raw_bytes, hashlib.sha256(raw_bytes).hexdigest()


def build_app_server_manifest(
    *,
    transcript_text: str,
    raw_sha256: str,
    thread_id: str,
    rendered: RenderedThread,
    scan_result: sensitivity.SensitiveScanResult | None,
    exported_at: datetime | str | None,
    app_server_warnings: Sequence[str] = (),
) -> export_manifest.ConversationExportManifest:
    """Build manifest metadata for the app-server thread/read adapter."""

    sensitivity_status = export_manifest.SENSITIVITY_UNSCANNED
    scan_metadata: dict[str, object] = {
        "status": export_manifest.SCAN_STATUS_NOT_SCANNED
    }
    warnings = [
        TRUST_STATE_UNVERIFIED_WARNING,
        *app_server_warnings,
        *rendered.warnings,
    ]
    if scan_result is not None:
        sensitivity_status = (
            export_manifest.SENSITIVITY_POTENTIAL
            if scan_result.findings
            else export_manifest.SENSITIVITY_NONE_DETECTED
        )
        scan_metadata = {
            "status": export_manifest.SCAN_STATUS_SCANNED,
            "scanner": "lrh_builtin_sensitive_scan",
            "scanner_version": 1,
            "finding_count": scan_result.finding_count,
            "categories": list(scan_result.categories),
        }
        if scan_result.findings:
            warnings.append(SENSITIVE_CONTENT_WARNING)

    return export_manifest.build_codex_manifest(
        transcript_text=transcript_text,
        source_sha256=raw_sha256,
        exported_at=exported_at,
        source_id=thread_id,
        source_adapter=SOURCE_ADAPTER,
        adapter_version=ADAPTER_VERSION,
        sensitivity=sensitivity_status,
        sensitivity_scan=scan_metadata,
        warnings=_dedupe_preserve_order(warnings),
        turn_count=rendered.turn_count,
        message_count=rendered.message_count,
    )


def render_thread(thread: Mapping[str, object]) -> RenderedThread:
    """Render a Codex thread object to Markdown body text."""

    warnings: list[str] = []
    message_count = 0
    item_type_counts: Counter[str] = Counter()
    turns = thread.get("turns")
    turn_list = turns if isinstance(turns, list) else []
    if turns is not None and not isinstance(turns, list):
        warnings.append("thread_turns_not_a_list")

    lines = [
        "# Codex Thread Export",
        "",
        f"- Thread ID: {_display_scalar(thread.get('id'))}",
        f"- Name: {_display_scalar(thread.get('name'))}",
        f"- Status: {_display_thread_status(thread.get('status'))}",
        f"- Turns: {len(turn_list)}",
        "",
        "This export is private, non-authoritative context. Reasoning items are "
        "omitted from the rendered Markdown by default; private raw JSON retains "
        "the original app-server response for local audit.",
    ]

    for turn_index, turn in enumerate(turn_list, start=1):
        if not isinstance(turn, Mapping):
            warnings.append("non_mapping_turn_omitted")
            continue
        status = turn.get("status")
        if isinstance(status, str) and status not in {"completed", "done"}:
            warnings.append(f"{NON_COMPLETED_TURN_WARNING_PREFIX}_{status}")
        lines.extend(
            [
                "",
                f"## Turn {turn_index}: {_display_scalar(turn.get('id'))}",
                "",
                f"- Status: {_display_scalar(status)}",
                f"- Started: {_display_scalar(turn.get('startedAt'))}",
                f"- Completed: {_display_scalar(turn.get('completedAt'))}",
            ]
        )
        items = turn.get("items")
        if not isinstance(items, list):
            warnings.append("turn_items_not_a_list")
            continue
        for item in items:
            if not isinstance(item, Mapping):
                warnings.append("non_mapping_item_omitted")
                continue
            item_type = item.get("type")
            item_type_name = item_type if isinstance(item_type, str) else "unknown"
            item_type_counts[item_type_name] += 1
            rendered_item = _render_item(item, item_type_name)
            warnings.extend(rendered_item.warnings)
            if rendered_item.is_message:
                message_count += 1
            lines.extend(["", *rendered_item.lines])

    body = "\n".join(lines).rstrip() + "\n"
    return RenderedThread(
        markdown_body=body,
        warnings=_dedupe_preserve_order(warnings),
        turn_count=len(turn_list),
        message_count=message_count,
        item_type_counts=dict(sorted(item_type_counts.items())),
    )


def render_export_markdown(
    transcript_text: str,
    manifest: export_manifest.ConversationExportManifest,
) -> str:
    """Render manifest frontmatter and transcript text as Markdown."""

    body = transcript_text if transcript_text.endswith("\n") else f"{transcript_text}\n"
    return f"{manifest.to_frontmatter()}\n{body}"


def run_export_codex_thread_cli(
    argv: Sequence[str] | None = None,
    *,
    prog: str,
) -> int:
    """Run the Codex app-server thread export CLI."""

    parser = argparse.ArgumentParser(
        prog=prog,
        description=(
            "Export a Codex thread through the Codex app-server thread/read API "
            "into private raw JSON and a manifest-backed Markdown artifact."
        ),
    )
    parser.add_argument(
        "--thread-id",
        default=None,
        help="Codex thread id to export (default: CODEX_THREAD_ID)",
    )
    parser.add_argument("--out", required=True, help="Markdown export output path")
    parser.add_argument(
        "--raw-out",
        required=True,
        help="private raw JSON capture output path",
    )
    parser.add_argument(
        "--codex",
        default=os.environ.get("CODEX", "codex"),
        help="Codex executable path (default: CODEX env var or codex)",
    )
    parser.add_argument("--force", action="store_true", help="overwrite outputs")
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=10.0,
        help="timeout for each app-server response (default: 10)",
    )
    parser.add_argument(
        "--no-scan-sensitive",
        action="store_true",
        help=(
            "skip the local heuristic sensitivity scanner and mark frontmatter "
            "sensitivity as unscanned"
        ),
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

    try:
        result = export_codex_thread(
            thread_id=identity.thread_id,
            output_path=Path(args.out),
            raw_output_path=Path(args.raw_out),
            codex_command=args.codex,
            force=args.force,
            scan_sensitive=not args.no_scan_sensitive,
            timeout_seconds=args.timeout_seconds,
        )
    except (OSError, CodexAppServerExportError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1

    if result.sensitivity_result is not None and result.sensitivity_result.findings:
        finding_count = len(result.sensitivity_result.findings)
        print(
            "warning: potential sensitive content detected "
            f"by heuristic scanner ({finding_count} finding(s))",
            file=sys.stderr,
        )
    if result.stderr_diagnostics:
        print(
            "warning: Codex app-server emitted stderr diagnostics: "
            f"{result.stderr_diagnostics}",
            file=sys.stderr,
        )

    print(f"Exported Codex thread: {args.out}")
    print(f"Raw capture: {args.raw_out}")
    print("Privacy: private")
    print(f"Sensitivity: {result.manifest.sensitivity}")
    print(f"Warnings: {len(result.manifest.warnings)}")
    print(f"Turns: {result.manifest.transcript_statistics.turn_count}")
    print(f"Messages: {result.manifest.transcript_statistics.message_count}")
    print(f"Item types: {_format_item_type_counts(result.item_type_counts)}")
    print(f"Source SHA-256: {result.raw_sha256}")
    return 0


@dataclasses.dataclass(frozen=True)
class _RenderedItem:
    lines: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    is_message: bool = False


def _render_item(item: Mapping[str, object], item_type: str) -> _RenderedItem:
    if item_type == "userMessage":
        return _render_message("User", item, is_message=True)
    if item_type == "agentMessage":
        return _render_message("Assistant", item, is_message=True)
    if item_type == "reasoning":
        return _RenderedItem(
            (
                "### Reasoning",
                "",
                "_Reasoning content omitted from rendered export._",
            ),
            (REASONING_OMITTED_WARNING,),
        )
    if item_type == "fileChange":
        return _RenderedItem(
            tuple(["### File Change", "", *_metadata_lines(item, _FILE_CHANGE_KEYS)]),
            (FILE_CHANGE_METADATA_WARNING,),
        )
    if item_type == "webSearch":
        return _RenderedItem(
            tuple(["### Web Search", "", *_metadata_lines(item, _WEB_SEARCH_KEYS)]),
            (WEB_SEARCH_METADATA_WARNING,),
        )
    if item_type == "contextCompaction":
        return _RenderedItem(
            tuple(
                [
                    "### Context Compaction",
                    "",
                    "A context compaction marker was present in this turn.",
                    *_metadata_lines(item, _CONTEXT_COMPACTION_KEYS),
                ]
            ),
            (CONTEXT_COMPACTION_WARNING,),
        )
    return _RenderedItem(
        (
            f"### Unknown Item: {item_type}",
            "",
            f"- Metadata keys: {', '.join(sorted(str(key) for key in item.keys()))}",
        ),
        (f"{UNKNOWN_ITEM_WARNING_PREFIX}_{item_type}",),
    )


_FILE_CHANGE_KEYS = (
    "path",
    "filePath",
    "kind",
    "status",
    "operation",
)
_WEB_SEARCH_KEYS = ("query", "title", "url", "status", "resultCount", "result_count")
_CONTEXT_COMPACTION_KEYS = ("status",)
_MESSAGE_TEXT_KEYS = (
    "text",
    "content",
    "message",
    "markdown",
    "body",
    "transcript",
)


def _render_message(
    heading: str,
    item: Mapping[str, object],
    *,
    is_message: bool,
) -> _RenderedItem:
    text = _extract_message_text(item)
    if text is None:
        return _RenderedItem(
            (f"### {heading}", "", "_No renderable text found in message item._"),
            (f"{heading.lower()}_message_text_missing",),
            is_message=is_message,
        )
    metadata = _message_metadata_lines(item)
    if metadata:
        return _RenderedItem(
            (f"### {heading}", "", *metadata, "", text.rstrip()),
            is_message=is_message,
        )
    return _RenderedItem(
        (f"### {heading}", "", text.rstrip()),
        is_message=is_message,
    )


def _message_metadata_lines(item: Mapping[str, object]) -> tuple[str, ...]:
    phase = item.get("phase")
    if isinstance(phase, str) and phase.strip():
        return (f"- Phase: {phase}",)
    return ()


def _extract_message_text(value: object) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        for key in _MESSAGE_TEXT_KEYS:
            text = _extract_message_text(value.get(key))
            if text:
                return text
        parts = []
        for key in ("parts", "messages", "items", "content"):
            nested = value.get(key)
            text = _extract_message_text(nested)
            if text:
                parts.append(text)
        if parts:
            return "\n\n".join(parts)
    if isinstance(value, list):
        parts = []
        for item in value:
            text = _extract_message_text(item)
            if text:
                parts.append(text)
        if parts:
            return "\n\n".join(parts)
    return None


def _metadata_lines(item: Mapping[str, object], keys: Sequence[str]) -> list[str]:
    lines = []
    for key in keys:
        if key in item:
            lines.append(f"- {key}: {_display_scalar(item[key])}")
    if not lines:
        lines.append(
            f"- Metadata keys: {', '.join(sorted(str(key) for key in item.keys()))}"
        )
    return lines


def _display_thread_status(value: object) -> str:
    if isinstance(value, Mapping):
        status_type = value.get("type")
        if isinstance(status_type, str):
            return status_type
    return _display_scalar(value)


def _display_scalar(value: object) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return json.dumps(value, sort_keys=True)


def _read_stderr_diagnostics(stderr_file: object) -> str | None:
    try:
        stderr_file.seek(0)
        data = stderr_file.read(MAX_STDERR_DIAGNOSTIC_BYTES + 1)
    except OSError as err:
        raise CodexAppServerExportError(
            "could not read app-server stderr diagnostics"
        ) from err
    if not isinstance(data, bytes) or not data:
        return None
    truncated = len(data) > MAX_STDERR_DIAGNOSTIC_BYTES
    if truncated:
        data = data[:MAX_STDERR_DIAGNOSTIC_BYTES]
    text = data.decode("utf-8", errors="replace").strip()
    if not text:
        return None
    safe_text = "".join(
        char if char in "\n\r\t" or char >= " " else "�" for char in text
    )
    if truncated:
        safe_text = f"{safe_text}\n[stderr diagnostics truncated]"
    return safe_text


def _format_item_type_counts(counts: Mapping[str, int]) -> str:
    if not counts:
        return "none"
    return ", ".join(
        f"{item_type}={count}" for item_type, count in sorted(counts.items())
    )


def _send_request(
    proc: subprocess.Popen[bytes],
    reader: JsonLineReader,
    *,
    request: Mapping[str, object],
    timeout_seconds: float,
) -> dict[str, Any]:
    _send_json_line(proc, request)
    request_id = request.get("id")
    deadline = time.monotonic() + timeout_seconds
    while True:
        response = reader.read_json_line(proc, deadline=deadline)
        if response.get("id") == request_id:
            return response


def _send_notification(
    proc: subprocess.Popen[bytes],
    notification: Mapping[str, object],
) -> None:
    _send_json_line(proc, notification)


def _send_json_line(
    proc: subprocess.Popen[bytes],
    payload: Mapping[str, object],
) -> None:
    if proc.stdin is None:
        raise CodexAppServerExportError("app-server stdin pipe was not created")
    try:
        proc.stdin.write((json.dumps(dict(payload)) + "\n").encode("utf-8"))
        proc.stdin.flush()
    except (BrokenPipeError, OSError) as err:
        raise CodexAppServerExportError("could not write to app-server stdin") from err


def _raise_for_json_rpc_error(response: Mapping[str, object], *, stage: str) -> None:
    if "error" in response:
        error = response.get("error")
        if isinstance(error, Mapping):
            message = error.get("message")
            code = error.get("code")
            raise CodexAppServerExportError(
                f"{stage} failed with JSON-RPC error {code}: {message}"
            )
        raise CodexAppServerExportError(f"{stage} failed with JSON-RPC error")
    result = response.get("result")
    if not isinstance(result, Mapping):
        raise CodexAppServerExportError(f"{stage} response missing result object")


def _thread_from_response(response: Mapping[str, object]) -> Mapping[str, object]:
    result = response.get("result")
    if not isinstance(result, Mapping):
        raise CodexAppServerExportError("thread/read response missing result object")
    thread = result.get("thread")
    if not isinstance(thread, Mapping):
        raise CodexAppServerExportError("thread/read response missing thread object")
    return thread


def _terminate_process(proc: subprocess.Popen[bytes]) -> None:
    if proc.stdin is not None:
        try:
            proc.stdin.close()
        except OSError:
            pass
    if proc.poll() is not None:
        if proc.stdout is not None:
            try:
                proc.stdout.close()
            except OSError:
                pass
        return
    proc.terminate()
    try:
        proc.wait(timeout=2.0)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=2.0)
    if proc.stdout is not None:
        try:
            proc.stdout.close()
        except OSError:
            pass


def _write_private_bytes(path: Path, data: bytes) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as output:
            fchmod = getattr(os, "fchmod", None)
            if fchmod is not None:
                try:
                    fchmod(output.fileno(), 0o600)
                except AttributeError:
                    pass
            output.write(data)
    except OSError as err:
        raise CodexAppServerExportError(f"Could not write raw capture: {path}") from err


def _codex_app_server_command(codex_command: Sequence[str] | str) -> list[str]:
    if isinstance(codex_command, str):
        command = [codex_command]
    else:
        command = list(codex_command)
    if not command or not all(part.strip() for part in command):
        raise CodexAppServerExportError("codex command must be non-empty")
    return [*command, "app-server", "--listen", "stdio://"]


def _exported_at_value(value: datetime | str | None) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise CodexAppServerExportError("exported_at must be timezone-aware")
        return value.isoformat()
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as err:
        raise CodexAppServerExportError(
            "exported_at must be an ISO-8601 datetime"
        ) from err
    if parsed.tzinfo is None:
        raise CodexAppServerExportError("exported_at must be timezone-aware")
    return value


def _normalized_non_empty(value: str, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise CodexAppServerExportError(f"{field} must be non-empty")
    return normalized


def _reject_existing_output(path: Path, force: bool) -> None:
    if path.exists() and not force:
        raise CodexAppServerExportError(f"Output already exists: {path}")


def _reject_unsafe_raw_output_path(original_path: Path, expanded_path: Path) -> None:
    if not original_path.expanduser().is_absolute():
        raise CodexAppServerExportError(
            "Raw output path must be absolute and outside the current Git worktree"
        )

    git_root = _current_git_worktree_root()
    if git_root is None:
        return
    try:
        raw_path = expanded_path.resolve(strict=False)
    except OSError:
        raw_path = expanded_path.absolute()
    if raw_path == git_root or git_root in raw_path.parents:
        raise CodexAppServerExportError(
            "Raw output path must be outside the current Git worktree"
        )


def _current_git_worktree_root() -> Path | None:
    try:
        current = Path.cwd().resolve(strict=False)
    except OSError:
        current = Path.cwd().absolute()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def _reject_output_collision(markdown_path: Path, raw_path: Path) -> None:
    if markdown_path.exists() and raw_path.exists():
        try:
            if markdown_path.samefile(raw_path):
                raise CodexAppServerExportError(
                    "Markdown output and raw output must be different files"
                )
        except OSError:
            pass
    try:
        same_path = markdown_path.resolve(strict=False) == raw_path.resolve(
            strict=False
        )
    except OSError:
        same_path = markdown_path.absolute() == raw_path.absolute()
    if same_path:
        raise CodexAppServerExportError(
            "Markdown output and raw output must be different files"
        )


def _dedupe_preserve_order(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(result)
