---
resolution: null
blocked_reason: null
blocked: false
id: WI-SESSION-ARCHIVE-SYNC-CAPTURE
title: Both-identifier session capture and minimal project/sessions/ index
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
  - project/design/proposals/proposed/lrh-execution-sessions/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - write_docs
forbidden_actions:
  - force_push
  - delete_branch
  - implement_lrh_sessions_sync
  - implement_lrh_sessions_discover_link
  - implement_lrh_sessions_report
  - implement_scheduled_or_hook_sync
  - modify_session_transcript_schema
acceptance:
  - /lrh-implement record-creation and /lrh-closeout both capture CLAUDE_CODE_HOST_SESSION_ID (host, session_transcript pointer) and CLAUDE_CODE_SESSION_ID (child, index alias) when available
  - A minimal project/sessions/ index exists recording, per session, the host id, child id(s), title, and PRs, with fields for branch/writtenBranches[]/PR to support later fork stitching
  - No changes to the session_transcript scalar/sequence grammar or its validator rules
  - Any edit to src/lrh/skills/lrh-closeout/ is mirrored identically in .claude/skills/lrh-closeout/, verified by diff -r exiting 0
  - lrh validate passes with 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/skills/lrh-implement/SKILL.md
  - .claude/skills/lrh-implement/SKILL.md
  - src/lrh/skills/lrh-closeout/SKILL.md
  - .claude/skills/lrh-closeout/SKILL.md
  - project/sessions/
---

# Both-identifier session capture and minimal project/sessions/ index

## Summary

Extend `/lrh-implement` execution-record creation and `/lrh-closeout` to
capture both the host and child Claude Code session identifiers, and
introduce a minimal `project/sessions/` index that persists the child id as
an alias of the host-keyed `session_transcript` pointer.

## Problem / Context

`PROP-LRH-SESSION-ARCHIVE-SYNC` (merged #436) found that 118 execution
records carry `claude-app:` host-id pointers but only a fraction resolve to
an on-disk transcript by filename, because transcript files are named by a
different, *child* SDK session id — and nothing durably records the mapping
between the two. The proposal's Decision 1 identifies capturing both ids at
record-creation/closeout time as the forward fix, and its Implementation Plan
puts this first and standalone, with no dependency on the archive reconciler
(Stage 2) or scheduling (Stage 4). The resolved fork-representation question
(PR #451) additionally requires that the index this item introduces support
stitching entries by shared `branch`/`writtenBranches[]`/PR from the start,
since Stage 3 will build on this schema rather than replace it. Governing
workstream: `WS-SESSION-ARCHIVE-SYNC`.

### Duplication search
- In-repo: No existing implementation found. `WI-CLOSEOUT-SESSION-SOURCING`
  (resolved, PR #431) made `/lrh-closeout` backend-aware and source the host
  id from `$CLAUDE_CODE_HOST_SESSION_ID`, but does not capture or persist the
  child id — this item extends that work, not duplicates it.
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed.

### Demand search
- Work items: None found — this is the first Stage-1 leaf of
  `WS-SESSION-ARCHIVE-SYNC`.
- Proposals: `PROP-LRH-SESSION-ARCHIVE-SYNC` (Decision 1, Decision 4,
  Implementation Plan Stage 1) is the governing design.
- Backlog: No matching entries.
- Recommendation: No action.

## Scope

- Capture `CLAUDE_CODE_HOST_SESSION_ID` and `CLAUDE_CODE_SESSION_ID` at
  execution-record creation (`/lrh-implement`) and at closeout
  (`/lrh-closeout`).
- Introduce a minimal `project/sessions/` index that persists the child id as
  an alias of the host-keyed pointer, with fields to support future
  branch/PR fork stitching (Stage 3 will enrich, not introduce, this schema).
- Update both `src/lrh/skills/` and `.claude/skills/` mirrors for any skill
  touched.

## Required Changes

1. Extend `/lrh-implement`'s execution-record creation step to also read
   `CLAUDE_CODE_SESSION_ID` and pass it through to the record/index step.
2. Extend `/lrh-closeout` Step 3 (already backend-aware per PR #431) to
   additionally capture the child id for the index, alongside its existing
   host-id resolution. Per the design's permissive-with-a-gate note, ask for
   explicit approval before any change to `/lrh-closeout` beyond this scope.
3. Define and create the minimal `project/sessions/` index (format/location
   under `project/sessions/`) recording, per session: host id, child id(s),
   title, PRs, and branch/`writtenBranches[]` fields for later stitching.
4. Update `src/lrh/skills/lrh-implement/references/execution-session-reference.md`
   and the `lrh-closeout` reference docs (both mirrors) to describe the new
   capture behavior and the index.
5. Add unit tests covering the capture logic and index writes.

## Non-Goals

- Does not implement `lrh sessions sync`, `discover`, `link`, or `report` —
  Stage 2/3 of `WS-SESSION-ARCHIVE-SYNC`.
- Does not implement the weekly scheduled sync or the `SessionEnd` hook —
  Stage 4.
- Does not change the `session_transcript` scalar/sequence grammar or its
  `lrh validate` rules — the pointer format is unchanged.
- Does not build the archive store itself (raw-JSONL mirror, `/export`
  metadata harvest) — Stage 2.
- Does not resolve the archive-root-location open question — unrelated to
  this item's index, which records ids and metadata, not transcript content.

## Acceptance Criteria

- `/lrh-implement` and `/lrh-closeout` both capture `CLAUDE_CODE_HOST_SESSION_ID`
  and `CLAUDE_CODE_SESSION_ID` when available.
- A minimal `project/sessions/` index exists and is populated for sessions
  processed after this item lands, with branch/PR stitching fields present
  (even if unused until Stage 3).
- No change to the `session_transcript` grammar or validator.
- `diff -r src/lrh/skills/lrh-closeout/ .claude/skills/lrh-closeout/` (and
  `lrh-implement/` equivalent) exits 0.
- `lrh validate` passes with 0 errors.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `diff -r src/lrh/skills/lrh-closeout/ .claude/skills/lrh-closeout/`
- `diff -r src/lrh/skills/lrh-implement/ .claude/skills/lrh-implement/`

## Risk Notes

- Touching `/lrh-closeout` risks scope creep into Stage 2/3/4 territory;
  `forbidden_actions` and the permissive-with-a-gate note bound this.
- The index schema chosen here is load-bearing for Stage 3 — getting the
  branch/PR stitching fields right now avoids a breaking schema change later.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-SESSION-ARCHIVE-SYNC.md`
- Design: `project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md`
