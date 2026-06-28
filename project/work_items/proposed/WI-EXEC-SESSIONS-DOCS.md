---
resolution: null
blocked_reason: null
blocked: false
id: WI-EXEC-SESSIONS-DOCS
title: Document execution session fields in README and PROMPTS
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
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - write_docs
forbidden_actions:
  - force_push
  - delete_branch
  - implement_schema_validation
  - implement_session_discovery
acceptance:
  - project/executions/README.md documents agent, instruction_source, and session_transcript optional fields with allowed values and examples
  - PROMPTS.md describes the three-phase execution session model (design / instruction / execution) for Claude.app sessions
  - PROMPTS.md documents the three new optional fields and the claude-app:<session-id> short form
  - lrh validate passes with 0 errors after the edits
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - project/executions/README.md
  - PROMPTS.md
---

# WI-EXEC-SESSIONS-DOCS: Document execution session fields in README and PROMPTS

## Summary

Stage 1 of PROP-LRH-EXECUTION-SESSIONS. Updates the two canonical
documentation files to describe the three-phase execution session model
and the three new optional execution-record fields (`agent`,
`instruction_source`, `session_transcript`) introduced by that proposal.

## Problem / Context

As of 2026-06-28, 163 execution records already use the new optional
fields (populated by `/lrh-implement`), but neither
`project/executions/README.md` nor `PROMPTS.md` mentions them. The
fields are documented only inside
`.claude/skills/lrh-implement/references/execution-session-reference.md`,
which is skill-internal and not the canonical reference for contributors.

New contributors and future skill authors have no authoritative
documentation to follow for how to populate `agent`,
`instruction_source`, or `session_transcript` in an execution record, or
what the three-phase execution session model is.

## Scope

- Edit `project/executions/README.md` — add the three optional fields
  to the front-matter schema section with descriptions, allowed values,
  and an example.
- Edit `PROMPTS.md` — add a Claude.app session section describing the
  three-phase model (design → instruction → execution) and the new
  fields, including the `claude-app:<session-id>` short form for
  `session_transcript` and the privacy note about absolute paths.

No code changes. No validator changes (those are Stage 2, see
WI-EXEC-SESSIONS-SCHEMA).

## Required Changes

### `project/executions/README.md`

Add a new subsection under "Front matter schema" documenting the three
optional fields:

- `agent`: identifies the execution backend; allowed values:
  `claude_app`, `codex_cloud`, `manual`.
- `instruction_source`: reference to the instruction-phase artifact
  (prompt file path, work item ID, or Taurcode meta-prompt name).
- `session_transcript`: reference to the Claude.app session using the
  `claude-app:<session-id>` short form. Document that absolute paths
  (`~/.claude/...`) must not be committed; use `pending` if the session
  ID is not yet known.

Include a complete example record showing all three fields populated.

### `PROMPTS.md`

Add a section on Claude.app sessions that covers:

- The three-phase execution session model (design / instruction /
  execution) and what artifact each phase produces.
- How to use `lrh prompt label` and `lrh prompt check-execution` in a
  Claude.app session as the instruction-phase step.
- The three new optional fields with their allowed values and examples.
- The `session_transcript: pending` → `claude-app:<session-id>` update
  pattern.
- A note that `/lrh-implement` automates this workflow.

## Non-Goals

- No validator changes — those belong in WI-EXEC-SESSIONS-SCHEMA.
- No `lrh sessions discover` or `lrh sessions link` commands — Stage 3.
- No changes to `.claude/skills/lrh-implement/references/` — those
  files can remain as-is; this work item updates the canonical docs.

## Acceptance Criteria

- `project/executions/README.md` documents `agent`, `instruction_source`,
  and `session_transcript` optional fields with allowed values and at
  least one complete example.
- `PROMPTS.md` describes the three-phase execution session model
  (design / instruction / execution) for Claude.app sessions.
- `PROMPTS.md` documents the three new optional fields and the
  `claude-app:<session-id>` short form.
- `lrh validate` passes with 0 errors after the edits.

## Validation

- `lrh validate`
- `grep -n "agent\|session_transcript\|instruction_source" project/executions/README.md`
  — must return entries in the schema section
- `grep -ni "three.phase\|claude.app\|claude_app" PROMPTS.md`
  — must return entries

## Risk Notes

Low risk. Documentation-only change. The fields are already in active use;
this work item closes the documentation gap without changing any behavior.
