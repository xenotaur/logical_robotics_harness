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
  - lrh validate warns when agent: has an unrecognized value (not in {claude_app, codex_cloud, manual})
  - lrh validate warns when session_transcript: begins with /, ~, or a Windows drive letter and suggests the claude-app:<id> short form
  - lrh validate passes (no error) on records with valid or absent optional fields
  - Tests cover valid values, invalid agent enum, and absolute-path session_transcript
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
PROP-LRH-EXECUTION-SESSIONS. Issues warnings (not errors) for invalid
enum values and absolute paths in `session_transcript`.

## Problem / Context

`lrh validate` currently has no execution-record validation. The new
optional fields (`agent`, `instruction_source`, `session_transcript`)
introduced by PROP-LRH-EXECUTION-SESSIONS pass silently with any value.
This means:

- `agent: bad_backend` is silently accepted; `lrh search executions
  "claude_app"` would miss the record.
- `session_transcript: ~/.claude/projects/.../abc.jsonl` is silently
  accepted; the proposal explicitly requires this to be warned on as a
  privacy risk (absolute paths leak the author's username and workspace
  layout to anyone who clones the repository).

As of 2026-06-28, 163 execution records already use these fields in the
wild without any validation. Stage 2 adds advisory warnings that guide
future records toward consistent, correct values.

## Scope

Extend `src/lrh/control/validator.py` to add advisory warnings (not
errors) for execution records that contain:

1. `agent:` with a value outside `{claude_app, codex_cloud, manual}` —
   warn and list the valid values.
2. `session_transcript:` with a value that begins with `/`, `~`, or a
   Windows drive letter (e.g., `C:\`) — warn and suggest the
   `claude-app:<session-id>` short form.

Warnings (not errors) are appropriate because:
- The fields are optional and backward-compatible.
- The 163 existing records should not be retroactively broken.
- Records with `session_transcript: pending` (a common interim value)
  must remain valid.

Add tests for:
- Valid `agent` values (`claude_app`, `codex_cloud`, `manual`).
- Unknown `agent` value → warning.
- `session_transcript: claude-app:<id>` → no warning.
- `session_transcript: pending` → no warning.
- `session_transcript: ~/.claude/...` → warning.
- `session_transcript: /absolute/path` → warning.

## Required Changes

### `src/lrh/control/validator.py`

Add an execution-record validation function (or extend the existing
artifact dispatch) to:

1. Read execution-record YAML frontmatter from files under
   `project/executions/`.
2. If `agent` is present and not in `{claude_app, codex_cloud, manual}`,
   emit a warning.
3. If `session_transcript` is present and starts with `/`, `~`, or a
   Windows drive letter, emit a warning suggesting the short form.

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

- `lrh validate` warns when `agent:` has an unrecognized value (not in
  `{claude_app, codex_cloud, manual}`).
- `lrh validate` warns when `session_transcript:` begins with `/`, `~`,
  or a Windows drive letter, and suggests the `claude-app:<id>` short
  form.
- `lrh validate` passes (no error) on records with valid or absent
  optional fields.
- Tests cover valid values, invalid `agent` enum, and absolute-path
  `session_transcript`.
- `lrh validate` passes 0 errors on the full project after the change.

## Validation

- `scripts/test`
- `lrh validate`
- Manual: create a test execution record with `agent: bad_value` and
  confirm a warning appears; create one with
  `session_transcript: ~/.claude/projects/x/abc.jsonl` and confirm
  the path warning appears.

## Risk Notes

Medium risk on the Python side: need to ensure the validator correctly
identifies execution-record files (under `project/executions/`) without
accidentally processing other YAML files. The advisory-warning approach
(not errors) limits blast radius — existing records with valid or absent
fields are unaffected.
