---
id: WI-ANTIGRAVITY-EXPORT-DURABLE-ARCHIVE-DEFAULT
title: Make Antigravity conversation exports durable-archive-first by default
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-ANTIGRAVITY-CONVERSATION-EXPORT
related_design:
  - project/design/proposals/adopted/lrh-antigravity-conversation-exporter/00_proposal.md
  - project/design/proposals/adopted/lrh-conversations-storage-interop/00_proposal.md
  - project/design/proposals/adopted/lrh-session-archive-sync/00_proposal.md
depends_on:
  - WI-ANTIGRAVITY-CONVERSATION-EXPORT-SKILL
blocked_by: []
blocked: false
blocked_reason: null
resolution: null
expected_actions:
  - edit_file
  - add_cli_command
  - write_docs
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - commit_raw_transcript_data
acceptance:
  - "`export-antigravity-session` CLI subcommand defaults to a durable private session archive path (`<archive_root>/antigravity/exports/<YYYY>/<MM>/<session-id>.md`) derived via `resolve_archive_root()` when `--out` is omitted"
  - "`--out PATH` remains supported as an optional explicit destination override"
  - "`src/lrh/skills/lrh-antigravity-export/SKILL.md` and `.agents/skills/lrh-antigravity-export/SKILL.md` document `--out` as optional with the durable archive default"
  - "`lrh conversation inspect-export` verification steps remain supported for both default and overridden output paths"
  - "Unit tests in `tests/conversations_tests/antigravity_export_test.py` cover durable archive default resolution and `--out` overrides"
  - "`lrh validate` passes with 0 errors and 0 warnings"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/conversations/antigravity_export.py
  - src/lrh/skills/lrh-antigravity-export/SKILL.md
  - .agents/skills/lrh-antigravity-export/SKILL.md
  - tests/conversations_tests/antigravity_export_test.py
---

# WI-ANTIGRAVITY-EXPORT-DURABLE-ARCHIVE-DEFAULT: Make Antigravity conversation exports durable-archive-first by default

## Summary

Update `lrh conversation export-antigravity-session` and the `/lrh-antigravity-export` skill package so that exports land in a durable, LRH-managed private session archive by default (derived via `resolve_archive_root()`), with `--out PATH` serving as an optional override rather than a mandatory argument.

## Problem / Context

Currently, `export-antigravity-session` requires `--out PATH` as a mandatory CLI argument. When omitted, the CLI fails with a missing option error. Because there is no default destination, callers must invent output paths manually — which can result in writing directly into application data directories (e.g. `~/.gemini/antigravity/brain/<session-id>/`), scratch folders, or ephemeral temp locations.

By contrast, Codex export (`archive-codex-thread`) calls `resolve_archive_root()` (`src/lrh/prompt_workflow_sessions.py`) and writes exports to a durable date-partitioned subtree (`<archive_root>/codex/exports/<YYYY>/<MM>/<export-id>/`) by default, treating `--out` as an override (established in `WI-CODEX-EXPORT-DURABLE-ARCHIVE-DEFAULT` and PR #579).

Establishing a durable-archive default for Antigravity exports aligns Antigravity with LRH session archive standards and fulfills a key prerequisite for any future multi-backend unifying `/lrh-export` CLI command.

### Prior Art Check
- **Verdict**: Performed (no duplication found).
- **Search**: Surveyed `WI-CODEX-EXPORT-DURABLE-ARCHIVE-DEFAULT`, `WI-SESSION-SYNC-JULES-INGESTION`, and `WS-SESSION-ARCHIVE-SYNC`. Confirmed no existing work item handles Antigravity durable archive defaults.

## Scope

### Included
- Update `run_convert_antigravity_session_cli` in `src/lrh/conversations/antigravity_export.py` to make `--out` optional.
- Integrate `resolve_archive_root()` to generate default output paths under `<archive_root>/antigravity/exports/<YYYY>/<MM>/<session-id>.md`.
- Update `src/lrh/skills/lrh-antigravity-export/SKILL.md` and `.agents/skills/lrh-antigravity-export/SKILL.md` to present `--out` as optional.
- Add CLI unit test coverage for default durable path resolution and `--out` overrides in `tests/conversations_tests/antigravity_export_test.py`.

### Non-Goals
- Building a unifying multi-backend `/lrh-export` command (blocked until all backend durable defaults land).
- Building Codex-style export import/rescue tooling for Antigravity (not required for Antigravity's usage model).

## Required Changes

### Component 1: Exporter Engine & CLI Wiring (`src/lrh/conversations/antigravity_export.py`)
- Import `resolve_archive_root` from `lrh.prompt_workflow_sessions`.
- Update CLI argument parser to make `--out` optional (`required=False`, `default=None`).
- If `out` is `None`, resolve output path as `resolve_archive_root() / "antigravity" / "exports" / YYYY / MM / f"{session_id}.md"`.

### Component 2: Native Skill Package (`src/lrh/skills/lrh-antigravity-export/SKILL.md` & `.agents/skills/`)
- Update frontmatter `argument-hint` to `"[--out OUTPUT.md] [--transcript-path PATH | --conversation-id ID | --latest]"`.
- Document durable archive default behavior when `--out` is omitted.

### Component 3: Unit Tests (`tests/conversations_tests/antigravity_export_test.py`)
- Add test verifying `export-antigravity-session` without `--out` writes to `<archive_root>/antigravity/exports/<YYYY>/<MM>/<session_id>.md`.
- Add test verifying explicit `--out` overrides the default path.

## Acceptance Criteria

1. `export-antigravity-session` CLI subcommand defaults to a durable private session archive path (`<archive_root>/antigravity/exports/<YYYY>/<MM>/<session-id>.md`) derived via `resolve_archive_root()` when `--out` is omitted.
2. `--out PATH` remains supported as an optional explicit destination override.
3. `src/lrh/skills/lrh-antigravity-export/SKILL.md` and `.agents/skills/lrh-antigravity-export/SKILL.md` document `--out` as optional with the durable archive default.
4. `lrh conversation inspect-export` verification steps remain supported for both default and overridden output paths.
5. Unit tests in `tests/conversations_tests/antigravity_export_test.py` cover durable archive default resolution and `--out` overrides.
6. `lrh validate` passes with 0 errors and 0 warnings.

## Validation

- `PYTHONPATH=src scripts/test tests/conversations_tests/antigravity_export_test.py`
- `PYTHONPATH=src scripts/test`
- `scripts/format --check`
- `scripts/lint`
- `lrh validate`

## Risk Notes

- Ensure `resolve_archive_root()` creates missing year/month directory parents automatically.
- Ensure output files created under default archive paths enforce restrictive permissions (`umask 077` / mode `0600`).
