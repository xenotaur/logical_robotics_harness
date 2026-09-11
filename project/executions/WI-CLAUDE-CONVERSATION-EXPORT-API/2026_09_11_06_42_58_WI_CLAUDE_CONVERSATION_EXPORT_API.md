---
execution_id: 2026_09_11_06_42_58_WI_CLAUDE_CONVERSATION_EXPORT_API
prompt_id: PROMPT(WI-CLAUDE-CONVERSATION-EXPORT-API:WI_CLAUDE_CONVERSATION_EXPORT_API)[2026-09-11T06:20:43+00:00]
work_item: WI-CLAUDE-CONVERSATION-EXPORT-API
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/664
commit: 
created_at: 2026-09-11T06:42:58+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-CLAUDE-CONVERSATION-EXPORT-API.md
session_transcript: claude-app:3278dd49-9852-4955-b978-00367552dc27
---

# Summary

Implement Tranche 1 of `PROP-LRH-CLAUDE-CONVERSATION-EXPORTER`: a core
Python API in `src/lrh/conversations/claude_export.py` that converts a
local Claude Code session JSONL transcript into a private,
non-authoritative Markdown export artifact, mirroring
`antigravity_export.py`'s structure.

# Result

Implemented via `/lrh-execute`'s inlined `/lrh-implement`:

- `src/lrh/conversations/claude_export.py` (new, 485 lines):
  `convert_claude_session()`, `_resolve_transcript_path()` (explicit
  path / session-id glob, erroring on >1 match / latest by mtime),
  `resolve_claude_archive_root()`, record-classification rendering
  (skip `queue-operation`, use `ai-title` as H1, skip `attachment`
  unless `include_system_attachments=True`, render `user`/`assistant`
  content blocks: text/tool_use/tool_result/thinking), subagent
  transcript referencing (default) and inlining
  (`include_subagents=True`).
- `src/lrh/conversations/export_manifest.py`: added `KIND_CLAUDE` and
  `SOURCE_TOOL_CLAUDE_CODE`, appended to `SUPPORTED_KINDS`/
  `SUPPORTED_SOURCE_TOOLS` — purely additive, no other manifest logic
  touched.
- `src/lrh/conversations/__init__.py`: wired `ClaudeExport`,
  `ClaudeExportError`, `convert_claude_session`,
  `resolve_claude_archive_root` into imports and `__all__`.
- `tests/conversations_tests/claude_export_test.py` (new, 15 tests):
  basic conversion, file-not-found, output collision, malformed-line
  warnings, queue-operation/attachment skipping,
  `include_system_attachments`, `ai-title` heading, tool_use/tool_result
  rendering, subagent referencing and inlining, transcript-path
  resolution (session-id, latest, multi-match error), archive-root
  worktree rejection, manifest constant registration.

**Pre-push diff-mode self-review** (`/lrh-implement` Step 7.5, the one
proactive trigger point) found one low-severity observation:
`claude_export.py` defines its own local `ADAPTER_VERSION` constant
rather than reusing `export_manifest.ADAPTER_VERSION`, unlike
`antigravity_export.py`. Independently re-verified directly (grep
confirmed both files' actual content). Judged not worth changing:
`codex_file_export.py` already uses the identical local-constant
pattern, so this is a pre-existing split in the codebase between two
adapters, not a deviation from one established convention — "fixing"
it would just pick a side of an already-inconsistent precedent.

Publication: pushed directly, PR opened at
https://github.com/xenotaur/logical_robotics_harness/pull/664.

# Validation

- `PYTHONPATH=src python -m pytest tests/conversations_tests/ -q` — 128
  passed (15 new, 113 pre-existing, no regressions).
- `lrh validate` — 0 errors, 0 warnings.
- `scripts/format --check --diff` / `scripts/lint` — blocked in this
  environment by a pre-existing `required-version` pin in
  `pyproject.toml`'s `[tool.black]`/`[tool.ruff]` sections (installed
  `black` 25.11.0 vs pinned `26.3.1`, `ruff` 0.15.0 vs pinned 0.15.12),
  unrelated to this diff — same environment condition already
  documented in prior `_REVIEW`/`_CONFIRM` records this session. Ran
  `black`/`ruff` directly against a temporary version-unlocked config
  (same `line-length`/`target-version` rules, no version pin) as a
  follow-up diagnostic: found and fixed two real formatting issues
  (`SUPPORTED_SOURCE_TOOLS` line length in `export_manifest.py`, an
  error-message line and a list-literal line in `claude_export.py`);
  clean on re-check.
- `python -m pylint --disable=all --enable=E,W src/lrh/conversations/claude_export.py` — 10.00/10.
- Manual `inspect_export` verification via
  `test_convert_claude_session_basic`: `Source hash: match`.

# Follow-up

- Two dependent work items remain: `WI-CLAUDE-CONVERSATION-EXPORT-CLI`
  (depends on this WI) and `WI-CLAUDE-CONVERSATION-EXPORT-SKILL`
  (depends on the CLI item).
- Continue `/lrh-execute`'s chain: Step 4 (`/lrh-land`) for PR #664.
