"""Unit tests for Antigravity conversation export API."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from lrh.conversations import (
    antigravity_export,
    export_inspector,
    export_manifest,
)


def _write_transcript(tmp_path: Path, lines: list[dict | str]) -> Path:
    transcript_file = tmp_path / "transcript.jsonl"
    content_lines: list[str] = []
    for item in lines:
        if isinstance(item, str):
            content_lines.append(item)
        else:
            content_lines.append(json.dumps(item))
    transcript_file.write_text("\n".join(content_lines) + "\n", encoding="utf-8")
    return transcript_file


def test_convert_antigravity_session_basic(tmp_path: Path) -> None:
    steps = [
        {
            "step_index": 0,
            "source": "USER_EXPLICIT",
            "type": "USER_INPUT",
            "status": "DONE",
            "content": "Hello, please list files.",
        },
        {
            "step_index": 1,
            "source": "MODEL",
            "type": "PLANNER_RESPONSE",
            "status": "DONE",
            "thinking": "User wants file listing.",
            "tool_calls": [
                {
                    "name": "list_dir",
                    "args": {"DirectoryPath": "/tmp"},
                }
            ],
        },
    ]
    source_file = _write_transcript(tmp_path, steps)
    out_file = tmp_path / "export.md"

    res = antigravity_export.convert_antigravity_session(
        source_file,
        output_path=out_file,
        source_id="test_session_123",
        exported_at="2026-08-08T12:00:00Z",
    )

    assert out_file.exists()
    assert res.manifest.source_tool == "antigravity"
    assert res.manifest.source_adapter == "antigravity_transcript_jsonl"
    assert res.manifest.kind == "lrh_antigravity_conversation_export"
    assert res.manifest.source_id == "test_session_123"
    assert res.manifest.transcript_statistics.turn_count == 1
    assert "## User" in res.markdown
    assert "Hello, please list files." in res.markdown
    assert "## Assistant" in res.markdown
    assert "Thinking" in res.markdown
    assert "list_dir" in res.markdown

    # Verify compatibility with inspect_export
    inspection = export_inspector.inspect_export(out_file, source_path=source_file)
    assert inspection.valid
    assert inspection.manifest_valid
    assert inspection.source_hash.status == "match"


def test_convert_antigravity_session_file_not_found(tmp_path: Path) -> None:
    missing = tmp_path / "non_existent.jsonl"
    with pytest.raises(
        antigravity_export.AntigravityExportError, match="does not exist"
    ):
        antigravity_export.convert_antigravity_session(missing)


def test_convert_antigravity_session_output_collision(tmp_path: Path) -> None:
    source_file = _write_transcript(
        tmp_path,
        [{"step_index": 0, "source": "USER", "type": "USER_INPUT", "content": "hi"}],
    )
    out_file = tmp_path / "export.md"
    out_file.write_text("existing content", encoding="utf-8")

    with pytest.raises(FileExistsError, match="already exists"):
        antigravity_export.convert_antigravity_session(
            source_file, output_path=out_file
        )

    # Force overwrite succeeds
    res = antigravity_export.convert_antigravity_session(
        source_file, output_path=out_file, force=True
    )
    assert "## User" in res.markdown


def test_convert_antigravity_session_malformed_lines_warning(tmp_path: Path) -> None:
    source_file = _write_transcript(
        tmp_path,
        [
            {
                "step_index": 0,
                "source": "USER",
                "type": "USER_INPUT",
                "content": "valid step",
            },
            "this is not valid json {{{",
        ],
    )
    res = antigravity_export.convert_antigravity_session(source_file)
    assert len(res.manifest.warnings) == 1
    assert "line 2: invalid JSON" in res.manifest.warnings[0]


def test_convert_antigravity_session_derive_source_id(tmp_path: Path) -> None:
    nested_dir = tmp_path / "brain" / "sess_abc123" / ".system_generated" / "logs"
    nested_dir.mkdir(parents=True)
    source_file = nested_dir / "transcript.jsonl"
    source_file.write_text(
        json.dumps({"step_index": 0, "source": "USER", "content": "hello"}) + "\n",
        encoding="utf-8",
    )

    res = antigravity_export.convert_antigravity_session(source_file)
    assert res.manifest.source_id == "sess_abc123"
