---
resolution: null
blocked_reason: null
blocked: false
id: WI-CLAUDE-CONVERSATION-EXPORT-CLI
title: Implement lrh conversation export-claude-session CLI subcommand
type: deliverable
status: proposed
owner: null
contributors: []
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design:
  - project/design/proposals/proposed/lrh-claude-conversation-exporter/00_proposal.md
depends_on:
  - WI-CLAUDE-CONVERSATION-EXPORT-API
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - add_cli_command
  - write_docs
forbidden_actions:
  - force_push
  - delete_branch
  - implement_lrh_claude_export_skill
acceptance:
  - "CLI subcommand lrh conversation export-claude-session is registered in src/lrh/cli/main.py"
  - "Discovery flags --transcript-path / --session-id / --latest are mutually exclusive"
  - "--session-id errors on more than one match instead of silently picking one"
  - "docs/reference/cli/conversation.md documents the new subcommand"
  - "lrh validate reports 0 errors"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/cli/main.py
  - docs/reference/cli/conversation.md
---

# WI-CLAUDE-CONVERSATION-EXPORT-CLI: Implement lrh conversation export-claude-session CLI subcommand

## Summary

Implement Tranche 2 of `PROP-LRH-CLAUDE-CONVERSATION-EXPORTER`: register the `export-claude-session` subcommand under `lrh conversation` in `src/lrh/cli/main.py`, backed by the `WI-CLAUDE-CONVERSATION-EXPORT-API` core API, and document it.

## Problem / Context

`WI-CLAUDE-CONVERSATION-EXPORT-API` provides the core conversion function but no user-facing entry point. Users need `lrh conversation export-claude-session` to export sessions, mirroring `export-antigravity-session`'s CLI shape.

### Duplication search
- In-repo: `export-antigravity-session` is the direct structural precedent, registered in `src/lrh/cli/main.py:157-161`.
- Sibling repos: None identified.
- External libraries: Not applicable.
- Recommendation: Proceed.

### Demand search
- Work items: `WI-CLAUDE-CONVERSATION-EXPORT-API` (dependency).
- Proposals: `PROP-LRH-CLAUDE-CONVERSATION-EXPORTER` Implementation Plan item 2.
- Backlog: No matching entries.
- Recommendation: No action; implements the proposal directly.

## Scope

- Register `export-claude-session` under `conversation_subparsers` in `src/lrh/cli/main.py`.
- Add its own new `docs/reference/cli/conversation.md` section (this item's own new command — not the pre-existing Antigravity gap, which is `WI-CLI-REFERENCE-ANTIGRAVITY-EXPORT-DOC-GAP`).
- Excludes the skill package (Tranche 3).

## Required Changes

1. Implement `run_convert_claude_session_cli(argv, *, prog)` in `src/lrh/conversations/claude_export.py`.
2. Register `export-claude-session` under `conversation` subparsers in `src/lrh/cli/main.py`, alongside `export-antigravity-session` (`src/lrh/cli/main.py:115-161`), and wire the dispatch branch near `main.py:1150`.
3. Implement discovery flags `--transcript-path` / `--session-id` / `--latest`, mutually exclusive, per the proposal's Design Decision 3.
4. Implement `--app-data-dir` (default `${CLAUDE_CONFIG_DIR:-~/.claude}`), `--out`, `--archive-root`, `--force`, `--source-id`, `--no-scan-sensitive`, `--include-system-attachments`, `--include-subagents`.
5. `--session-id` resolves by globbing `<app-data-dir>/projects/*/<id>.jsonl`; more than one match is an error requiring `--transcript-path` to disambiguate, not a silent first-match pick.
6. Add a `##`-level `lrh conversation export-claude-session` section to `docs/reference/cli/conversation.md`, matching the depth of the existing Codex/Antigravity sections.
7. Add CLI-level tests under `tests/conversations_tests/claude_export_test.py` (or a dedicated CLI test module) covering `--help`, discovery flag mutual exclusivity, and the `--session-id` collision error.

## Non-Goals

- Does not implement the skill package — that is `WI-CLAUDE-CONVERSATION-EXPORT-SKILL`.
- Does not address the pre-existing `export-antigravity-session` doc gap — that is `WI-CLI-REFERENCE-ANTIGRAVITY-EXPORT-DOC-GAP`.

## Acceptance Criteria

- `lrh conversation export-claude-session --help` displays help documentation.
- `--transcript-path` / `--session-id` / `--latest` are enforced as mutually exclusive.
- `--session-id` matching more than one project directory errors rather than picking silently.
- `docs/reference/cli/conversation.md` documents the new subcommand.
- `lrh validate` reports 0 errors.

## Validation

- `lrh conversation export-claude-session --help`
- `scripts/test tests/conversations_tests/claude_export_test.py`
- `lrh validate`
