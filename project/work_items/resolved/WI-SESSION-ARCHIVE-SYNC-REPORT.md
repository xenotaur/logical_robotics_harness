---
resolution: "Implemented and merged in PR #607 (commit 2f1a1840f43408327b26c77d2a8dd16ed8394749)"
blocked_reason: null
blocked: false
id: WI-SESSION-ARCHIVE-SYNC-REPORT
title: lrh sessions report and archive index enrichment
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
  - WI-SESSION-ARCHIVE-SYNC-RECONCILER
  - WI-SESSION-SYNC-NESTED-ARTIFACTS
blocked_by: []
expected_actions:
  - edit_file
  - add_cli_command
  - run_tests
  - write_docs
forbidden_actions:
  - force_push
  - delete_branch
  - implement_scheduled_or_hook_sync
  - modify_session_transcript_schema
  - migrate_existing_archive_layout
acceptance:
  - project/sessions index enrichment supports report needs for session_transcript pointers, branch/PR stitching, and archive presence without changing the session_transcript field grammar
  - lrh sessions report identifies dangling session_transcript pointers and unarchived repo-changing sessions using the existing private archive/index model
  - The report is deterministic and suitable for closeout/dogfood review without printing raw transcript bodies
  - Stage 4 scheduling and closeout-triggered sync remain out of scope
  - lrh validate passes with 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/prompt_workflow_sessions.py
  - src/lrh/sessions_workflow.py
  - tests/assist_tests/prompt_workflow_sessions_test.py
  - tests/cli_tests/sessions_test.py
---

# lrh sessions report and archive index enrichment

## Summary

Implement Stage 3 of `WS-SESSION-ARCHIVE-SYNC`: enrich the session archive
index enough to support an `lrh sessions report` command that surfaces dangling
session pointers and missing private archive coverage without exposing raw
transcript bodies.

## Problem / Context

`WI-SESSION-ARCHIVE-SYNC-CAPTURE`, `WI-SESSION-ARCHIVE-SYNC-RECONCILER`,
`WI-CODEX-EXPORT-DURABLE-ARCHIVE-DEFAULT`, and
`WI-SESSION-SYNC-NESTED-ARTIFACTS` established durable local capture, archive
sync/discover/link, Codex durable export defaults, and nested artifact
coverage. The active workstream now needs its next actionable leaf so Stage 3
can close the observability gap: users need a report that says which execution
records still dangle and which repo-changing sessions are not archived.

### Duplication search

- In-repo: No active/proposed work item currently owns Stage 3 report/index
  enrichment. Existing resolved leaves deliberately left `lrh sessions report`
  as a non-goal.
- Sibling repos: None identified.
- External libraries: None identified; this is LRH control-plane/archive
  reconciliation logic.
- Recommendation: Proceed.

### Demand search

- Workstreams: `WS-SESSION-ARCHIVE-SYNC` lists Stage 3 index enrichment plus
  `lrh sessions report` as required exit-criteria scope.
- Proposals: `PROP-LRH-SESSION-ARCHIVE-SYNC` governs the archive/index/report
  direction.
- Backlog: No separate matching backlog item identified during this closeout.
- Recommendation: File this leaf and keep Stage 4 separate.

## Scope

- Enrich the existing `project/sessions/` index or supporting archive metadata
  only as much as needed for deterministic reporting.
- Add `lrh sessions report`.
- Report dangling `session_transcript` pointers and unarchived repo-changing
  sessions for work produced after Stage 1 lands.
- Keep report output metadata-oriented and safe for terminal inspection.

## Required Changes

1. Review the current Stage 1/2 session index and private archive layout.
2. Define the minimal additional index/archive metadata needed for report
   output, preserving the existing `session_transcript` pointer grammar.
3. Implement `lrh sessions report` in the existing sessions CLI surface.
4. Add tests for dangling pointer detection, archive-presence detection, and
   safe metadata-only output.
5. Update relevant command/reference documentation if the command shape or
   fields need explanation.

## Non-Goals

- Do not implement weekly scheduled sync.
- Do not wire `/lrh-closeout` to invoke `lrh sessions sync`.
- Do not implement a `SessionEnd` hook.
- Do not commit raw transcript bodies to the repository.
- Do not change the `session_transcript` scalar/sequence grammar.
- Do not migrate existing private archive layout unless a narrow metadata
  read/update is required for the report.

## Acceptance Criteria

- `lrh sessions report` identifies dangling `session_transcript` pointers.
- `lrh sessions report` identifies unarchived repo-changing sessions in the
  Stage 1+ data set.
- Report output does not print raw transcript bodies.
- Tests cover the report's positive and clean cases.
- `lrh validate` passes with 0 errors.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`

## Risk Notes

- The report will be used for closeout/dogfood review, so false confidence is
  worse than a conservative warning. Prefer explicit "unknown" or "not enough
  metadata" states over silently treating missing data as clean.
- Keep Stage 4 scheduling and closeout integration separate so this item stays
  reviewable.
