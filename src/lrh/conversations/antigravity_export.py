"""Convert local Google Antigravity session transcripts to Markdown export artifacts."""

from __future__ import annotations

import dataclasses
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from lrh.conversations import export_manifest, sensitivity

DEFAULT_ADAPTER_NAME = "antigravity_transcript_jsonl"


class AntigravityExportError(ValueError):
    """Raised when an Antigravity transcript export fails."""


@dataclasses.dataclass(frozen=True)
class AntigravityExport:
    """Result of converting an Antigravity JSONL session transcript to Markdown."""

    markdown: str
    manifest: export_manifest.ConversationExportManifest
    sensitivity_result: sensitivity.SensitiveScanResult | None


def convert_antigravity_session(
    transcript_path: Path,
    *,
    output_path: Path | None = None,
    force: bool = False,
    scan_sensitive: bool = True,
    source_id: str | None = None,
    exported_at: str | None = None,
) -> AntigravityExport:
    """Convert an Antigravity transcript.jsonl file into a private Markdown export."""

    path = transcript_path.expanduser()
    if not path.exists():
        raise AntigravityExportError(f"transcript file does not exist: {path}")
    if not path.is_file():
        raise AntigravityExportError(f"transcript path is not a file: {path}")

    try:
        raw_bytes = path.read_bytes()
    except OSError as err:
        raise AntigravityExportError(f"could not read transcript file: {path}") from err

    source_sha256 = hashlib.sha256(raw_bytes).hexdigest()

    try:
        raw_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as err:
        raise AntigravityExportError(
            f"transcript file is not valid UTF-8: {path}"
        ) from err

    lines = raw_text.splitlines()
    warnings: list[str] = []
    steps: list[dict[str, object]] = []

    for index, line in enumerate(lines, start=1):
        line_str = line.strip()
        if not line_str:
            continue
        try:
            parsed = json.loads(line_str)
            if isinstance(parsed, dict):
                steps.append(parsed)
            else:
                warnings.append(f"line {index}: JSON item is not an object")
        except json.JSONDecodeError as err:
            warnings.append(f"line {index}: invalid JSON: {err}")

    if not steps and not warnings:
        warnings.append("transcript file contains no valid step objects")

    rendered_body = _render_antigravity_transcript(steps)
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
        kind=export_manifest.KIND_ANTIGRAVITY,
        schema_version=export_manifest.SCHEMA_VERSION,
        source_tool=export_manifest.SOURCE_TOOL_ANTIGRAVITY,
        source_adapter=DEFAULT_ADAPTER_NAME,
        privacy=export_manifest.DEFAULT_PRIVACY,
        authority=export_manifest.DEFAULT_AUTHORITY,
        sensitivity=sensitivity_status,
        source_id=source_id or _derive_source_id(path),
        adapter_version=export_manifest.ADAPTER_VERSION,
        warnings=tuple(warnings),
    )

    full_markdown = f"{manifest_obj.to_frontmatter()}\n{body}"

    if output_path is not None:
        out = output_path.expanduser()
        if out.exists() and not force:
            raise FileExistsError(f"output path already exists: {out}")
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            out.write_text(full_markdown, encoding="utf-8")
        except OSError as err:
            raise AntigravityExportError(
                f"could not write output export file: {out}"
            ) from err

    return AntigravityExport(
        markdown=full_markdown,
        manifest=manifest_obj,
        sensitivity_result=scan_res,
    )


def _derive_source_id(path: Path) -> str | None:
    """Derive session conversation ID from Antigravity path structure if possible."""
    parts = path.parts
    for i, part in enumerate(parts):
        if part == "brain" and i + 1 < len(parts):
            return parts[i + 1]
    return None


def _count_turns(steps: Sequence[dict[str, object]]) -> int:
    """Count user turns in step payload."""
    return sum(1 for step in steps if step.get("source") in ("USER_EXPLICIT", "USER"))


def _count_messages(steps: Sequence[dict[str, object]]) -> int:
    """Count user, planner, and system message steps."""
    return sum(
        1
        for step in steps
        if step.get("type") in ("USER_INPUT", "PLANNER_RESPONSE", "MODEL", "SYSTEM")
    )


def _render_antigravity_transcript(steps: Sequence[dict[str, object]]) -> str:
    """Render Antigravity JSONL step objects into readable Markdown."""
    lines: list[str] = ["# Antigravity Session Transcript", ""]

    for step in steps:
        source = str(step.get("source", ""))
        step_type = str(step.get("type", ""))
        content = step.get("content")
        thinking = step.get("thinking")
        tool_calls = step.get("tool_calls")

        if source in ("USER_EXPLICIT", "USER") or step_type == "USER_INPUT":
            lines.append("## User")
            lines.append("")
            if isinstance(content, str) and content.strip():
                lines.append(content.strip())
                lines.append("")

        elif source == "MODEL" or step_type in ("PLANNER_RESPONSE", "MODEL"):
            lines.append("## Assistant")
            lines.append("")
            if isinstance(thinking, str) and thinking.strip():
                lines.append("> **Thinking**")
                for tline in thinking.strip().splitlines():
                    lines.append(f"> {tline}")
                lines.append("")
            if isinstance(content, str) and content.strip():
                lines.append(content.strip())
                lines.append("")
            if isinstance(tool_calls, list) and tool_calls:
                lines.append("### Tool Calls")
                lines.append("")
                for tc in tool_calls:
                    if isinstance(tc, dict):
                        name = tc.get("name", "tool")
                        args = tc.get("args", {})
                        lines.append(f"- **`{name}`**")
                        if args:
                            args_json = json.dumps(args, indent=2)
                            lines.append("  ```json")
                            for aline in args_json.splitlines():
                                lines.append(f"  {aline}")
                            lines.append("  ```")
                lines.append("")

        elif step_type not in ("CONVERSATION_HISTORY", "SYSTEM"):
            if isinstance(content, str) and content.strip():
                lines.append(f"### Result ({step_type})")
                lines.append("")
                lines.append("```")
                lines.append(content.strip())
                lines.append("```")
                lines.append("")

    return "\n".join(lines)
