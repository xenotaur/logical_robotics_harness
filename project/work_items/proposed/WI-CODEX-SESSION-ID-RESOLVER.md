---
resolution: null
blocked_reason: null
blocked: false
id: WI-CODEX-SESSION-ID-RESOLVER
title: Add Codex session ID resolver skill and CLI helper
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
  - WS-SESSION-ARCHIVE-SYNC
related_design:
  - project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md
  - project/design/proposals/adopted/lrh-codex-app-server-conversation-export/00_proposal.md
  - docs/conversations/codex_export.md
  - docs/reference/cli/conversation.md
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - add_cli_command
  - write_docs
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - commit_raw_transcript_data
  - scrape_codex_storage_internals
acceptance:
  - A shared resolver returns the same Codex task/thread id source that `/lrh-codex-export` uses when no explicit id is supplied
  - '`/lrh-codex-session` reports the current `codex-app:<id>` session transcript pointer without exporting transcript content'
  - '`/lrh-codex-export` references or uses the shared resolver contract instead of carrying independent session-id instructions'
  - CLI and/or library tests cover `CODEX_THREAD_ID` present, missing, and whitespace-only behavior
  - Docs explain that the returned id is a Codex task/thread pointer, not an export attempt id or transcript artifact path
  - '`lrh validate` passes with 0 errors'
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/conversations/
  - src/lrh/cli/main.py
  - src/lrh/skills/lrh-codex-session/SKILL.md
  - src/lrh/skills/lrh-codex-export/SKILL.md
  - .agents/skills/lrh-codex-session/SKILL.md
  - .agents/skills/lrh-codex-export/SKILL.md
  - .claude/skills/lrh-codex-session/SKILL.md
  - .claude/skills/lrh-codex-export/SKILL.md
  - .gemini/plugins/lrh/skills/lrh-codex-session/SKILL.md
  - .gemini/plugins/lrh/skills/lrh-codex-export/SKILL.md
  - docs/conversations/codex_export.md
  - docs/reference/cli/conversation.md
  - tests/cli_tests/
  - tests/conversations_tests/
---

## Summary

Add a small shared Codex task/thread ID resolver and a `/lrh-codex-session`
skill so LRH closeout records can capture `codex-app:<id>` without forcing an
early `/lrh-codex-export`.

## Problem / Context

`/lrh-codex-export` already defaults its export target from `CODEX_THREAD_ID`,
and both Codex export CLI entry points use the same environment variable as the
default `--thread-id`. Closeout records, however, often need the
`session_transcript` pointer before the transcript should be exported; exporting
early creates duplicate per-attempt archive artifacts if the session is exported
again at closeout. A shared resolver lets closeout and export use the same Codex
task/thread identity while keeping export attempts separate from session
identity.

`WS-SESSION-ARCHIVE-SYNC` already owns the governing invariant that repo-changing
agent sessions should not be lost, and existing closeout guidance already
permits `codex-app:<task-or-thread-id>` when a durable Codex app identifier is
available. This work item turns that currently manual convention into a small
reusable Codex-facing workflow.

### Duplication search

- In-repo: No existing `/lrh-codex-session` skill or shared current Codex thread
  resolver was found. Related code exists in
  `src/lrh/conversations/codex_app_server_export.py`,
  `src/lrh/conversations/codex_archive.py`, and
  `src/lrh/skills/lrh-codex-export/SKILL.md`; those surfaces already consume
  `CODEX_THREAD_ID` but do not expose a transcript-pointer-only resolver.
- Sibling repos: None identified.
- External libraries: None identified. This is LRH-specific policy and skill/CLI
  integration around Codex's current task/thread environment.
- Recommendation: Proceed by extracting the existing `CODEX_THREAD_ID`
  convention into a shared LRH resolver and thin skill, not by creating another
  export path.

### Demand search

- Work items: No existing proposed work item was found for a Codex session ID
  resolver. Related resolved items include `WI-CODEX-CONVERSATION-EXPORT-SKILL`,
  `WI-CODEX-EXPORT-DURABLE-ARCHIVE-DEFAULT`, and
  `WI-CLOSEOUT-SESSION-ALIAS-BACKEND-SCOPE`.
- Proposals: Related demand exists in `PROP-LRH-SESSION-ARCHIVE-SYNC` and the
  adopted Codex app-server export proposal, which establish private transcript
  capture and Codex app-server export behavior.
- Backlog: Found matching backlog demand in `project/design/backlog.md` for a
  Codex-specific `codex-app:<id>` / `pending` / `none` transcript resolution
  path.
- Recommendation: Link this item to `WS-SESSION-ARCHIVE-SYNC`; do not auto-close
  the broader backlog note until the implementation lands and is assessed
  against the remaining Codex-specific skill gaps.

## Scope

- Add a small library and/or CLI resolver for the current Codex task/thread id.
- Add `/lrh-codex-session` as a metadata-only skill that reports the closeout-ready
  `codex-app:<id>` pointer.
- Update `/lrh-codex-export` so its Step 1 identity logic references or uses the
  same resolver contract.
- Document that this id is the export target and closeout pointer, not an export
  attempt id, archive directory, raw JSON path, or transcript artifact.
- Add focused tests for resolver behavior and CLI output.

## Required Changes

1. Add a small resolver in `src/lrh/conversations/` that normalizes an explicit
   thread id or `CODEX_THREAD_ID`, rejects empty/whitespace-only values, and
   returns both the raw thread id and `codex-app:<id>` pointer form.
2. Add or extend an `lrh conversation` CLI command, such as
   `current-codex-thread-id`, with metadata-only output modes suitable for
   scripts and skills.
3. Add `src/lrh/skills/lrh-codex-session/SKILL.md` as a thin workflow wrapper
   that reports the current Codex task/thread id and the
   `session_transcript: codex-app:<id>` value without exporting transcript
   content.
4. Update `src/lrh/skills/lrh-codex-export/SKILL.md` so its thread-id resolution
   points to the shared resolver contract instead of duplicating independent
   instructions.
5. Mirror touched skills into installed skill targets present in the repo,
   including `.agents/skills/`, `.claude/skills/`, and
   `.gemini/plugins/lrh/skills/` where applicable.
6. Update `docs/conversations/codex_export.md` and
   `docs/reference/cli/conversation.md` to describe the resolver, pointer format,
   and difference between session identity and export attempts.
7. Add tests covering explicit id, `CODEX_THREAD_ID` present, missing env var,
   whitespace-only env var, CLI output, and transcript-body non-disclosure.

## Non-Goals

- Do not export, inspect, print, or commit transcript content.
- Do not create or modify archive directories as part of `/lrh-codex-session`.
- Do not use archive directory names, `attempt.json`, raw JSON paths, or
  timestamps as session identity.
- Do not scrape undocumented Codex app storage internals.
- Do not implement target-aware `/lrh-export` for all backends.
- Do not change the backend-agnostic `session_transcript` grammar beyond
  documenting this Codex app resolver path.
- Do not implement closeout-triggered session sync or scheduled archive sync.

## Acceptance Criteria

- A shared resolver returns the same Codex task/thread id source that
  `/lrh-codex-export` uses when no explicit id is supplied.
- `/lrh-codex-session` reports the current `codex-app:<id>` session transcript
  pointer without exporting transcript content.
- `/lrh-codex-export` references or uses the shared resolver contract instead of
  carrying independent session-id instructions.
- CLI and/or library tests cover `CODEX_THREAD_ID` present, missing, and
  whitespace-only behavior.
- Docs explain that the returned id is a Codex task/thread pointer, not an
  export attempt id or transcript artifact path.
- `lrh validate` passes with 0 errors.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `lrh conversation current-codex-thread-id --help`
- `lrh skills check --target claude --local`
- `lrh skills check --target codex --local`
- `lrh skills check --target antigravity --local`

## Risk Notes

- The name "session id" can be misleading if users confuse Codex task/thread
  identity with an export attempt. The implementation should consistently
  distinguish `codex-app:<id>` from archive paths and attempt metadata.
- If `CODEX_THREAD_ID` is absent, the resolver should fail clearly or ask for an
  explicit id; it should not guess from local storage.
- Duplicating resolver prose between skills would recreate the drift this item
  is meant to avoid, so `/lrh-codex-export` should cite or call the shared
  contract.
- Metadata-only output matters: this helper should be safe to run during
  closeout without exposing transcript bodies.
