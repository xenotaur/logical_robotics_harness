---
resolution: "Implemented and merged in PR #612 (commit 2711d2997)"
blocked_reason: null
blocked: false
id: WI-SESSION-ARCHIVE-SYNC-SCHEDULED-CLOSEOUT-SYNC
title: Session archive scheduled and closeout-triggered sync
type: deliverable
status: resolved
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
depends_on:
  - WI-SESSION-ARCHIVE-SYNC-REPORT
blocked_by: []
expected_actions:
  - edit_file
  - add_cli_command
  - write_docs
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - commit_raw_transcripts
  - change_session_transcript_schema
  - implement_encrypted_off_machine_archive
acceptance:
  - /lrh-closeout invokes lrh sessions sync, or an equivalent documented LRH command path, so successful closeout attempts refresh the private session archive before the session can decay
  - A documented weekly scheduled lrh sessions sync path exists for sessions that never reach closeout, with setup, inspection, and disable instructions suitable for local developer machines
  - The implementation preserves private local archive policy and never commits raw transcript bodies to the repository
  - The SessionEnd hook remains optional and is either explicitly deferred or implemented only as an accelerant, not as the sole retention guarantee
  - lrh sessions report can be used after the scheduled/closeout sync path to inspect remaining archive coverage gaps without printing transcript bodies
  - lrh validate passes with 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/skills/lrh-closeout/SKILL.md
  - .claude/skills/lrh-closeout/SKILL.md
  - docs/reference/cli/sessions.md
  - tests/
---

# Session archive scheduled and closeout-triggered sync

## Summary

Implement Stage 4 of `WS-SESSION-ARCHIVE-SYNC`: make session archive sync happen
at closeout time and provide a weekly scheduled sync path, preserving the
private local archive model and leaving `SessionEnd` as an optional latency
accelerant.

## Problem / Context

Stages 1 through 3 delivered forward session identity capture, archive
sync/discover/link, durable Codex export defaults, nested artifact coverage,
and `lrh sessions report`. The governing proposal's retention invariant still
requires one more piece: capture must not depend solely on a human remembering
to run a command or on a PR reaching closeout before local transcript retention
expires.

`PROP-LRH-SESSION-ARCHIVE-SYNC` Decision 6 chose both closeout-triggered sync
and weekly scheduled sync. Closeout-triggered sync ties capture to the normal
landing workflow; weekly scheduled sync protects sessions that never reach
closeout. The optional `SessionEnd` hook can reduce latency, but cannot replace
the weekly guarantee.

## Scope

- Wire `/lrh-closeout` or its backing LRH command path to invoke
  `lrh sessions sync` at the appropriate closeout point.
- Add a documented weekly scheduled `lrh sessions sync` path for local developer
  machines.
- Keep raw transcripts in the private archive only; committed repository state
  remains metadata-only.
- Preserve the current `session_transcript` grammar.

## Required Changes

1. Identify the safest closeout integration point for invoking
   `lrh sessions sync`, including behavior when the private archive root is
   missing, inaccessible, or explicitly disabled.
2. Implement closeout-triggered sync with a human-visible outcome in closeout
   reporting.
3. Add a weekly scheduled sync setup path, including setup, inspection, and
   disable documentation.
4. Ensure `lrh sessions report` remains the verification command after sync and
   does not print raw transcript bodies.
5. Add focused tests for the closeout integration path and any scheduler
   command/config generation added by the implementation.
6. If any `src/lrh/skills/` closeout instructions are touched, mirror the
   corresponding project-local skill content where required by repository
   convention.

## Non-Goals

- Does not implement encrypted or off-machine backups.
- Does not commit raw transcript bodies to the repository.
- Does not change execution-record schema or `session_transcript` pointer
  grammar.
- Does not require a `SessionEnd` hook; that hook remains optional.
- Does not require migrating existing private archive contents.

## Acceptance Criteria

- Closeout-triggered sync is implemented or documented through a concrete LRH
  command path, with clear behavior for unavailable archive roots.
- Weekly scheduled sync has a documented setup/inspection/disable path.
- Raw transcripts remain private local artifacts and are not committed.
- `lrh sessions report` remains the human-safe inspection path after sync.
- Tests cover the new command or workflow behavior.
- `lrh validate` passes with 0 errors.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`

## Risk Notes

- Closeout is already a gated workflow; adding sync there must not silently
  block or mutate repository state in surprising ways when private archive
  storage is unavailable.
- Scheduler setup is host-specific. Prefer an explicit, inspectable command or
  generated configuration over opaque background behavior.
- The retention guarantee depends on weekly sync being easy to verify and easy
  to disable.

## Related Workstream and Designs

- Workstream: `project/workstreams/active/WS-SESSION-ARCHIVE-SYNC.md`
- Design: `project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md`
