---
resolution: null
blocked_reason: null
blocked: false
id: WI-EXEC-SESSIONS-SCHEMA
title: Add lrh validate support for execution session optional fields
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
  - WS-EXECUTION-FRAMEWORK
related_design:
  - project/design/proposals/proposed/lrh-execution-sessions/00_proposal.md
depends_on:
  - WI-EXEC-SESSIONS-DOCS
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - write_docs
forbidden_actions:
  - force_push
  - delete_branch
  - implement_session_discovery
  - implement_lrh_sessions_command
acceptance:
  - lrh validate accepts session_transcript values of the form <backend>:<id> (any scheme, e.g. claude-app, codex-cloud, chatgpt) and the sentinels pending and none without warning
  - lrh validate warns when session_transcript begins with /, ~, or a Windows drive letter and suggests the <backend>:<id> short form
  - lrh validate warns when session_transcript is a non-sentinel value lacking a <scheme>: prefix (e.g. a bare id)
  - lrh validate does not warn on any non-empty agent value, since the schema is open-ended (claude_app | codex_cloud | manual | <other>) per PROP-LRH-EXECUTION-SESSIONS
  - Tests cover each known scheme, pending, none, absolute-path and bare-id session_transcript, and claude_app/codex_cloud/manual/<other> agent values
  - lrh validate passes 0 errors on the full project after the change
required_evidence:
  - test_output
  - lrh_validate
artifacts_expected:
  - src/lrh/control/validator.py
  - tests/
---

# WI-EXEC-SESSIONS-SCHEMA: Add lrh validate support for execution session optional fields

## Summary

Stage 2 of PROP-LRH-EXECUTION-SESSIONS. Adds execution-record
validation logic to `lrh validate` for the three optional fields
(`agent`, `instruction_source`, `session_transcript`) defined by
PROP-LRH-EXECUTION-SESSIONS. Issues advisory warnings (not errors) that
enforce the **backend-agnostic session pointer grammar** — the
`<backend>:<id>` scheme plus the `pending`/`none` sentinels — recorded in
the 2026-07-23 "Backend-Agnostic Session Pointer Grammar" decision-log
entry (`project/memory/decision_log.md`) and documented in
`project/executions/README.md`.

## Problem / Context

`lrh validate` currently has no execution-record validation. The new
optional fields (`agent`, `instruction_source`, `session_transcript`)
introduced by PROP-LRH-EXECUTION-SESSIONS pass silently with any value.
This means:

- `session_transcript: ~/.claude/projects/.../abc.jsonl` is silently
  accepted; the proposal explicitly requires this to be warned on as a
  privacy risk (absolute paths leak the author's username and workspace
  layout to anyone who clones the repository).
- A malformed `session_transcript` (a bare id with no `<scheme>:` prefix,
  or a stray value) is silently accepted, undermining the greppability the
  grammar is meant to guarantee.

**This work item was refreshed on 2026-07-25** to track the grammar as it
now stands, not the narrower Claude-only shape originally drafted. Two
things changed under it since:

- The canonical `session_transcript` grammar is now a scheme-prefixed
  scalar `<backend>:<id>` (schemes `claude-app:`, `codex-cloud:`,
  `chatgpt:`) plus **two** sentinels, `pending` and `none`, per the
  2026-07-23 decision-log entry. A validator that only recognizes
  `claude-app:` + `pending` (the original draft) would mis-handle the
  newer values.
- `agent` is **open-ended** by design (`claude_app | codex_cloud | manual
  | <other>` in PROP-LRH-EXECUTION-SESSIONS §fields), so a hard "unknown
  agent value" warning — as originally drafted — would fire on legitimate
  `<other>` backends. The refresh drops that hard warning.

As of 2026-07-25, 138 execution records carry these fields (134
`claude-app:` / `claude_app`, 4 `none` / `codex_cloud` from the Codex-era
backfill; 0 `pending`). The 4 `codex_cloud` + `none` records are exactly
the shape the original criteria did not anticipate. Stage 2 adds advisory
warnings that guide future records toward the grammar without breaking any
existing record.

## Scope

Extend `src/lrh/control/validator.py` to add advisory warnings (not
errors) for execution records that contain:

1. `session_transcript:` with a value that begins with `/`, `~`, or a
   Windows drive letter (e.g., `C:\`) — warn (privacy risk) and suggest
   the `<backend>:<id>` short form.
2. `session_transcript:` with a non-sentinel value that lacks a
   `<scheme>:` prefix (e.g. a bare id) — warn and suggest the
   `<backend>:<id>` form. `pending` and `none` are sentinels and never
   warn; any `<scheme>:<id>` value (`claude-app:`, `codex-cloud:`,
   `chatgpt:`, or a future scheme) is accepted without warning.

`agent` is intentionally **not** enum-validated: the field is open-ended
(`claude_app | codex_cloud | manual | <other>`), so any non-empty value
is accepted without warning. (Documenting the known values belongs to
`WI-EXEC-SESSIONS-DOCS`, not to a validator warning.)

Warnings (not errors) are appropriate because:
- The fields are optional and backward-compatible.
- The 138 existing records should not be retroactively broken.
- The sentinels `pending` and `none` must remain valid.

Add tests for:
- `session_transcript: claude-app:<id>` → no warning.
- `session_transcript: codex-cloud:<id>` → no warning.
- `session_transcript: chatgpt:<id>` → no warning.
- `session_transcript: pending` → no warning.
- `session_transcript: none` → no warning.
- `session_transcript: ~/.claude/...` → warning (absolute path).
- `session_transcript: /absolute/path` → warning (absolute path).
- `session_transcript: bareid` (no scheme, not a sentinel) → warning.
- `agent:` values `claude_app`, `codex_cloud`, `manual`, and an `<other>`
  value → no warning for any.

## Required Changes

### `src/lrh/control/validator.py`

Add an execution-record validation function (or extend the existing
artifact dispatch) to:

1. Read execution-record YAML frontmatter from files under
   `project/executions/`.
2. If `session_transcript` is present and starts with `/`, `~`, or a
   Windows drive letter, emit a privacy warning suggesting the
   `<backend>:<id>` short form.
3. If `session_transcript` is present, is not `pending` or `none`, and
   contains no `<scheme>:` prefix, emit a grammar warning.
4. Do not enum-validate `agent`; accept any non-empty value.

### Tests

Add tests in the appropriate test file under `tests/` covering the
cases listed in Scope above.

## Non-Goals

- No `lrh snapshot project` agent-count reporting — deferred.
- No `lrh sessions discover` or `lrh sessions link` — Stage 3
  (WI-EXEC-SESSIONS-DISCOVERY).
- Do not make the fields required — they remain optional.
- Do not convert existing records with valid values to errors.

## Acceptance Criteria

- `lrh validate` accepts `session_transcript` values of the form
  `<backend>:<id>` (any scheme, e.g. `claude-app:`, `codex-cloud:`,
  `chatgpt:`) and the sentinels `pending` and `none` without warning.
- `lrh validate` warns when `session_transcript` begins with `/`, `~`, or
  a Windows drive letter, and suggests the `<backend>:<id>` short form.
- `lrh validate` warns when `session_transcript` is a non-sentinel value
  lacking a `<scheme>:` prefix (e.g. a bare id).
- `lrh validate` does not warn on any non-empty `agent` value (the schema
  is open-ended: `claude_app | codex_cloud | manual | <other>`).
- `lrh validate` passes (no error) on records with valid or absent
  optional fields.
- Tests cover each known scheme, `pending`, `none`, absolute-path and
  bare-id `session_transcript`, and `claude_app`/`codex_cloud`/`manual`/
  `<other>` `agent` values.
- `lrh validate` passes 0 errors on the full project after the change.

## Validation

- `scripts/test`
- `lrh validate`
- Manual: create a test execution record with
  `session_transcript: ~/.claude/projects/x/abc.jsonl` and confirm the
  absolute-path warning appears; create one with
  `session_transcript: bareid` and confirm the grammar warning appears;
  create one with `session_transcript: none` and `agent: some_other`
  and confirm neither warns.

## Risk Notes

Medium risk on the Python side: need to ensure the validator correctly
identifies execution-record files (under `project/executions/`) without
accidentally processing other YAML files. The advisory-warning approach
(not errors) limits blast radius — existing records with valid or absent
fields are unaffected.
