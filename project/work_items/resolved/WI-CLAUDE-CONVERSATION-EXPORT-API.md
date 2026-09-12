---
resolution: "Implemented and merged in PR #664 (commit 07fbc9c5). Core Python API (claude_export.py) with record-classification rendering, subagent handling, and manifest support; two review rounds fixed 8 findings total including a P1 private-file-permissions race and a data-loss guard. One non-blocking follow-up (turn_count overcounting) tracked as a separate task."
blocked_reason: null
blocked: false
id: WI-CLAUDE-CONVERSATION-EXPORT-API
title: Implement Claude Code session export Python API
type: deliverable
status: resolved
owner: null
contributors: []
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design:
  - project/design/proposals/proposed/lrh-claude-conversation-exporter/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - implement_lrh_claude_conversation_export_cli
acceptance:
  - "src/lrh/conversations/claude_export.py exists with convert_claude_session(), _resolve_transcript_path(), resolve_claude_archive_root()"
  - "export_manifest.py gains KIND_CLAUDE = \"lrh_claude_conversation_export\" and SOURCE_TOOL_CLAUDE_CODE = \"claude_code\", appended to SUPPORTED_KINDS/SUPPORTED_SOURCE_TOOLS"
  - "Rendering skips queue-operation and attachment records by default, renders user/assistant content blocks, uses ai-title as heading when present"
  - "Output artifacts pass lrh conversation inspect-export verification"
  - "lrh validate reports 0 errors"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/conversations/claude_export.py
  - src/lrh/conversations/export_manifest.py
  - src/lrh/conversations/__init__.py
---

# WI-CLAUDE-CONVERSATION-EXPORT-API: Implement Claude Code session export Python API

## Summary

Implement Tranche 1 of `PROP-LRH-CLAUDE-CONVERSATION-EXPORTER`: a core Python API in `src/lrh/conversations/claude_export.py` that converts a local Claude Code session JSONL transcript into a private, non-authoritative Markdown export artifact.

## Problem / Context

Claude Code's own `/export` slash command is unavailable in the Claude Desktop app's Code-tab session surface. `PROP-LRH-CLAUDE-CONVERSATION-EXPORTER` (`status: proposed`) designs a repo-owned replacement, parallel to the adopted Antigravity and Codex exporters. This item implements the proposal's core-API tranche.

### Duplication search
- In-repo: No `src/lrh/conversations/claude_export.py` exists. `antigravity_export.py` is the direct structural precedent (459 lines: `convert_antigravity_session()`, `_render_antigravity_transcript()`, `_resolve_transcript_path()`, `resolve_antigravity_archive_root()`).
- Sibling repos: None identified.
- External libraries: None identified providing a stable, version-independent Claude Code transcript export API.
- Recommendation: Proceed.

### Demand search
- Work items: None found requesting this directly; this item is the direct implementation of `PROP-LRH-CLAUDE-CONVERSATION-EXPORTER`'s Implementation Plan item 1.
- Proposals: `PROP-LRH-CLAUDE-CONVERSATION-EXPORTER` (`status: proposed`).
- Backlog: No matching entries.
- Recommendation: No action; implements the proposal directly.

## Scope

- Add `src/lrh/conversations/claude_export.py` mirroring `antigravity_export.py`'s structure.
- Add `KIND_CLAUDE` and `SOURCE_TOOL_CLAUDE_CODE` constants to `src/lrh/conversations/export_manifest.py`.
- Wire new public names into `src/lrh/conversations/__init__.py`.
- Does not include the CLI subcommand (Tranche 2) or skill package (Tranche 3).

## Required Changes

1. Add `KIND_CLAUDE = "lrh_claude_conversation_export"` and `SOURCE_TOOL_CLAUDE_CODE = "claude_code"` to `src/lrh/conversations/export_manifest.py`, appended to `SUPPORTED_KINDS` and `SUPPORTED_SOURCE_TOOLS` (`export_manifest.py:13-18`) — purely additive, no other manifest changes needed.
2. Implement `convert_claude_session(transcript_path, *, output_path=None, force=False, scan_sensitive=True, source_id=None, exported_at=None, include_system_attachments=False, include_subagents=False)` in `src/lrh/conversations/claude_export.py`, following `convert_antigravity_session()`'s shape in `antigravity_export.py:35-154`.
3. Implement record classification per the proposal's Design Decision 4: render `user`/`assistant` records including nested content blocks (text, `tool_use`, `tool_result`, `thinking`); skip `queue-operation` records; use an `ai-title` record's value as the Markdown H1 when present; skip `attachment` records by default (`deferred_tools_delta`, `agent_listing_delta`, `mcp_instructions_delta`, `skill_listing`) unless `include_system_attachments=True`.
4. Implement subagent transcript handling per Design Decision 5: reference sibling `<session-id>/subagents/agent-<id>.jsonl` transcripts by id/description (read from the matching `.meta.json`'s `agentType`/`description` fields) by default; append full subagent transcripts as an appendix when `include_subagents=True`.
5. Implement `_resolve_transcript_path()` supporting explicit path, `--session-id` (glob `<app-data-dir>/projects/*/<id>.jsonl`, erroring on more than one match), and `--latest` (glob `<app-data-dir>/projects/*/*.jsonl` by mtime) — mirroring `antigravity_export.py:408-459`.
6. Implement `resolve_claude_archive_root()` targeting `<archive_root>/claude/exports/<YYYY>/<MM>/<session-id>.md`, mirroring `resolve_antigravity_archive_root()` in `antigravity_export.py:164-171`.
7. Compute `transcript_statistics`: `turn_count` = count of `type=="user"` records carrying a `message` field; `message_count` = count of `type in ("user","assistant")` records carrying `message`.
8. Reuse `sensitivity.py`, `DEFAULT_PRIVACY`, `DEFAULT_AUTHORITY`, the `umask 077`/`chmod 0600` private-file pattern, and `export_inspector.py` unchanged.
9. Export new public names (`ClaudeExport`, `ClaudeExportError`, `convert_claude_session`, `resolve_claude_archive_root`) from `src/lrh/conversations/__init__.py`.
10. Add unit tests under `tests/conversations_tests/claude_export_test.py` covering rendering, discovery, and manifest construction.

**Correction (supersedes item 7's `turn_count` description):** `turn_count`
no longer counts every `type=="user"` record carrying `message`, as
originally specified above. A `tool_result` reply is also delivered as a
`type=="user"` record whose `message.content` is a list containing a
`{"type": "tool_result", ...}` block, not human-typed text; counting it
overcounted real human turns whenever a session included tool calls.
`_count_turns()` in `src/lrh/conversations/claude_export.py` now counts only
`type=="user"` records whose `message.content` is a plain string, or a list
containing at least one non-`tool_result` block. Fixed in PR #665
(`fix(claude-export): exclude tool_result-only records from turn_count`),
flagged during this work item's own PR #664 self-review as non-blocking at
the time since it is a cosmetic/statistics-only field with no control-flow
impact.

## Non-Goals

- Does not implement the CLI subcommand — that is `WI-CLAUDE-CONVERSATION-EXPORT-CLI`.
- Does not implement the skill package — that is `WI-CLAUDE-CONVERSATION-EXPORT-SKILL`.
- Does not implement `SessionEnd` hook-based automatic capture — explicitly out of scope per the proposal's Non-Goals.

## Acceptance Criteria

- `src/lrh/conversations/claude_export.py` exists with `convert_claude_session()`, `_resolve_transcript_path()`, `resolve_claude_archive_root()`.
- `export_manifest.py` contains `KIND_CLAUDE` and `SOURCE_TOOL_CLAUDE_CODE`, appended to the supported-value tuples.
- A converted sample transcript passes `lrh conversation inspect-export` with `Source hash: match`.
- `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test tests/conversations_tests/claude_export_test.py`
