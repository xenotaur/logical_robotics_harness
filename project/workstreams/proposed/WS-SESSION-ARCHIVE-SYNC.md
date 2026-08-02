---
id: WS-SESSION-ARCHIVE-SYNC
kind: planning_node
title: Session Archive and Sync
status: proposed
stage: designed
origin: follow_up
summary: Deliver the session/PR/execution-record archive-and-sync system designed in PROP-LRH-SESSION-ARCHIVE-SYNC — durable local transcript archive, lrh sessions reconciler, non-authoritative project/sessions/ index, and both-identifier capture — so that no repo-changing agent session is ever lost.
parent_id: null
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_design:
  - project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md
  - project/design/proposals/proposed/lrh-execution-sessions/00_proposal.md
  - project/workstreams/proposed/WS-EXECUTION-FRAMEWORK.md
work_items: []
exit_criteria:
  - All four PROP-LRH-SESSION-ARCHIVE-SYNC stages are delivered as resolved work items (Stage 1 both-identifier capture + minimal project/sessions/ index; Stage 2 lrh sessions sync + discover/link; Stage 3 index enrichment + report; Stage 4 required weekly scheduled sync + optional SessionEnd hook)
  - Both open questions (archive-root location; fork representation) are resolved and recorded, with fork representation settled before Stage 3 is scoped
  - lrh sessions report shows no dangling session_transcript pointers and no unarchived repo-changing sessions for work produced after Stage 1 lands
  - lrh validate passes with 0 errors after each leaf lands
  - PROP-LRH-SESSION-ARCHIVE-SYNC implementation_status is advanced (implemented, with implemented_by referencing the resolved leaves) and its adoption decision is recorded
---

# Session Archive and Sync

## Purpose

This workstream coordinates the delivery of `PROP-LRH-SESSION-ARCHIVE-SYNC`
(merged in PR #436): a durable local archive for agent session transcripts, an
`lrh sessions` reconciler that keeps it aligned with the control plane, a
committed but non-authoritative `project/sessions/` index recording the
session → PR tree, and both-identifier (host + child) capture at execution-record
creation and closeout. Its governing invariant is that **no agent session that
changed this repository is ever lost.** It exists now because the proposal is
merged and reviewed, the motivating gap is measurably decaying (dangling-pointer
resolution fell 28% → 14% over six days against a ~30-day transcript-retention
window), and the design's own Implementation Plan splits cleanly into four
staged, independently reviewable leaves.

## Scope

- Deliver the four PROP-LRH-SESSION-ARCHIVE-SYNC stages as work items through the
  standard LRH execution lifecycle.
- Resolve and record the proposal's two open questions (archive-root location;
  fork representation) as they gate their dependent stages.
- Advance the proposal's `implementation_status` and record its adoption decision
  as the leaves land.

## Prior Art Check

### Duplication search
- In-repo: No duplicate implementation. This workstream governs delivery of
  `PROP-LRH-SESSION-ARCHIVE-SYNC`; the sibling `WS-EXECUTION-FRAMEWORK` owns the
  already-resolved session-id documentation/schema/closeout-sourcing work
  (`WI-EXEC-SESSIONS-DOCS`, `WI-EXEC-SESSIONS-SCHEMA`,
  `WI-CLOSEOUT-SESSION-SOURCING`), which this workstream builds on but does not
  duplicate.
- Sibling repos: None identified.
- External libraries: None identified for adoption as a whole; rsync/restic-style
  idempotent-mirror semantics are adopted internally per the proposal.
- Recommendation: Proceed.

### Demand search
- Work items: The scope formerly reserved as `WI-EXEC-SESSIONS-DISCOVERY` was
  retired by human decision on 2026-07-29 (recorded in
  `project/executions/AD_HOC/2026_07_29_15_08_45_WS_EXECUTION_FRAMEWORK_SESSION_WIS.md`);
  that id must not be reused. New leaves take fresh ids.
- Proposals: `PROP-LRH-SESSION-ARCHIVE-SYNC` is the governing design;
  `PROP-LRH-EXECUTION-SESSIONS` (Stage 3 amended to point here) and
  `PROP-LRH-CONVERSATIONS-STORAGE-INTEROP` (storage-class vocabulary) are related.
- Backlog: No matching entries.
- Recommendation: No action — the retired id is already reconciled and closed out.

## Work Items

No work-item files exist yet; the four leaves below will be filed via
`/lrh-work-item` as the workstream advances. **Provisional** names are given for
readability; none reuses the retired `WI-EXEC-SESSIONS-DISCOVERY` id.

- **Stage 1 — both-identifier capture + minimal index** (forward fix; standalone,
  first). Extend `/lrh-implement` record creation and `/lrh-closeout` to capture
  `CLAUDE_CODE_HOST_SESSION_ID` and `CLAUDE_CODE_SESSION_ID`, recording the host
  stem as the `session_transcript` pointer and persisting the child id in a
  minimal `project/sessions/` index. Because this modifies `/lrh-closeout`
  **by design**, its `forbidden_actions` must be *permissive-with-a-gate*
  ("ask for explicit approval before exceeding scope"), not a hard
  `modify_lrh_closeout_skill` prohibition.
- **Stage 2 — `lrh sessions sync` + `discover`/`link`.** Raw-JSONL mirror plus
  `/export` `metadata.json` harvest for the host↔child mapping. Acceptance
  criteria must include: (a) **append-safety** — a growing transcript is
  re-copied whenever the source has grown (compare size/mtime, not mere
  existence); archived copies are never truncated, shrunk, or deleted; (b)
  **complete child-id aliases** — collect aliases by scanning the distinct
  line-level `sessionId` values inside each JSONL, not just filename stems, so
  forked lineages are not left with incomplete alias sets.
- **Stage 3 — index enrichment + `report`.** Enrich the Stage 1 index
  (era-general keys, fork stitching, dedup latest-wins) and add
  `lrh sessions report`. **Blocked on the fork-representation open question**,
  which shapes the index schema.
- **Stage 4 — scheduling + hook.** The weekly scheduled `lrh sessions sync` is
  **required** (the guarantee for sessions that never reach closeout); the
  `SessionEnd` hook is the only optional piece. Any part touching `/lrh-closeout`
  carries the same permissive-with-a-gate rule as Stage 1.

## Exit Criteria

- All four stages above are delivered as resolved work items.
- Both open questions (archive-root location; fork representation) are resolved
  and recorded, with fork representation settled before Stage 3 is scoped.
- `lrh sessions report` shows no dangling `session_transcript` pointers and no
  unarchived repo-changing sessions for work produced after Stage 1 lands.
- `lrh validate` passes with 0 errors after each leaf lands.
- `PROP-LRH-SESSION-ARCHIVE-SYNC` `implementation_status` is advanced
  (`implemented`, with `implemented_by` referencing the resolved leaves) and its
  adoption decision is recorded.

## Non-Goals

- Does not commit session transcripts to the repository in any form (per the
  2026-07-23 decision-log entry) — the archive is private and local.
- Does not build the encrypted off-machine archive tier — permitted by the
  proposal but explicitly deferred.
- Does not reuse the retired `WI-EXEC-SESSIONS-DISCOVERY` id.
- Does not own the sibling session-id work (`WI-EXEC-SESSIONS-DOCS`,
  `WI-EXEC-SESSIONS-SCHEMA`, `WI-CLOSEOUT-SESSION-SOURCING`) — those belong to
  `WS-EXECUTION-FRAMEWORK`.
- Does not itself adopt `PROP-LRH-SESSION-ARCHIVE-SYNC` — adoption is a separate
  human decision, tracked as an exit criterion.

## Relationship to Design

- Governing proposal:
  `project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md`
- Amended prior proposal (Stage 3 points here):
  `project/design/proposals/proposed/lrh-execution-sessions/00_proposal.md`
- Sibling workstream (resolved session-id leaves):
  `project/workstreams/proposed/WS-EXECUTION-FRAMEWORK.md`

## Open Questions

- **Archive-root location.** Interacts with the user's backup and file-sync
  setup (in vs. outside a synced folder, given past sync-conflict issues) and
  with the eventual encrypted off-machine tier. Design-discussion item; the
  design assumes only that the root is configurable.
- **Fork representation.** Whether one work stretch spanning a fork is recorded
  as a sequence-valued `session_transcript` or as per-record ids stitched by the
  `project/sessions/` index via branch/PR. This shapes the Stage 3 index schema
  and must be resolved before Stage 3 is scoped.
