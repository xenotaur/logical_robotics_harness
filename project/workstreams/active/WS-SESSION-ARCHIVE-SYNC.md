---
id: WS-SESSION-ARCHIVE-SYNC
kind: planning_node
title: Session Archive and Sync
status: active
stage: executing
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
work_items:
  - WI-SESSION-ARCHIVE-SYNC-CAPTURE
  - WI-SESSION-ARCHIVE-SYNC-RECONCILER
  - WI-CODEX-EXPORT-DURABLE-ARCHIVE-DEFAULT
  - WI-SESSION-SYNC-NESTED-ARTIFACTS
  - WI-SESSION-ARCHIVE-SYNC-REPORT
  - WI-SESSION-ARCHIVE-SYNC-SCHEDULED-CLOSEOUT-SYNC
exit_criteria:
  - All four PROP-LRH-SESSION-ARCHIVE-SYNC stages are delivered as resolved work items (Stage 1 both-identifier capture + minimal project/sessions/ index with branch/PR stitching support; Stage 2 lrh sessions sync + discover/link; Stage 3 index enrichment + report; Stage 4 both required weekly scheduled sync and closeout-triggered sync, plus optional SessionEnd hook)
  - The archive-root-location open question is resolved and recorded (the index-regeneration-frequency open question is non-load-bearing and may be resolved informally during Stage 3 implementation)
  - /lrh-closeout invokes lrh sessions sync and a weekly scheduled sync is configured (Stage 4; both mandatory per Decision 6)
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
- Resolve and record the proposal's open archive-root-location question. (The
  proposal's index-regeneration-frequency question is explicitly non-load-bearing
  and does not gate this workstream's exit.)
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

Stage 1 is filed as `WI-SESSION-ARCHIVE-SYNC-CAPTURE` (resolved), Stage 2
as `WI-SESSION-ARCHIVE-SYNC-RECONCILER` (resolved), Stage 3 as
`WI-SESSION-ARCHIVE-SYNC-REPORT` (resolved), and Stage 4 as
`WI-SESSION-ARCHIVE-SYNC-SCHEDULED-CLOSEOUT-SYNC` (resolved). None reuses the
retired `WI-EXEC-SESSIONS-DISCOVERY` id.

- **Stage 1 — `WI-SESSION-ARCHIVE-SYNC-CAPTURE`: both-identifier capture +
  minimal index — resolved.** Merged via
  [PR #498](https://github.com/xenotaur/logical_robotics_harness/pull/498):
  `/lrh-implement` Step 9 and `/lrh-closeout` Step 3/5 both capture
  `CLAUDE_CODE_HOST_SESSION_ID` and `CLAUDE_CODE_SESSION_ID`, recording the
  host stem as the `session_transcript` pointer and persisting the child id
  as an alias in the new `project/sessions/index.jsonl` (via a dedicated
  `lrh prompt record-session-alias` CLI subcommand backed by
  `src/lrh/prompt_workflow_sessions.py`). Per the resolved
  fork-representation question (PR #451), the index schema supports
  stitching entries by shared `branch` / `written_branches[]` / PR from the
  start — fork continuity is expressed only in the index, never by editing
  an already-landed record's single-id `session_transcript`. Closeout
  records the child-id alias only on the same-window resolution path,
  never on cross-session or pasted-URL resolution.
- **Stage 2 — `WI-SESSION-ARCHIVE-SYNC-RECONCILER`: `lrh sessions sync` +
  `discover`/`link`.** Raw-JSONL mirror plus
  `/export` `metadata.json` harvest for the host↔child mapping. Acceptance
  criteria must include: (a) **append-safety** — a growing transcript is
  re-copied whenever the source has grown (compare size/mtime, not mere
  existence); archived copies are never truncated, shrunk, or deleted; (b)
  **complete child-id aliases** — collect aliases by scanning the distinct
  line-level `sessionId` values inside each JSONL, not just filename stems, so
  forked lineages are not left with incomplete alias sets.
- **Codex durable export default —
  `WI-CODEX-EXPORT-DURABLE-ARCHIVE-DEFAULT`.** Codex app-server exports use the
  same private session archive root resolver as `lrh sessions sync`
  (`--archive-root` > `LRH_SESSION_ARCHIVE_ROOT` >
  `~/.local/share/lrh/session-archive`), with Codex artifacts stored under
  `codex/exports/YYYY/MM/` and rescued imports under `codex/imports/YYYY/MM/`.
  This resolves the Codex-export durable-default question for local archive
  placement while leaving encrypted/off-machine backup policy deferred.
- **Stage 3 — `WI-SESSION-ARCHIVE-SYNC-REPORT`: index enrichment + `report`
  — resolved.** Enrich the Stage 1 index (era-general keys, branch/PR fork
  stitching per Decision 4, dedup latest-wins as needed for reporting) and add
  `lrh sessions report`.
- **Stage 4 —
  `WI-SESSION-ARCHIVE-SYNC-SCHEDULED-CLOSEOUT-SYNC`: scheduling + hook.** Per
  Decision 6, **both** scheduling paths are mandatory scope: the weekly
  scheduled `lrh sessions sync` (the guarantee for sessions that never reach
  closeout) **and** wiring `/lrh-closeout` to invoke `lrh sessions sync`
  (capture tied to the moment a PR lands). Only the `SessionEnd` hook is
  optional. Any part touching `/lrh-closeout` carries the same
  permissive-with-a-gate rule as Stage 1.

## Exit Criteria

- All four stages above are delivered as resolved work items.
- The archive-root-location open question is resolved and recorded.
- `/lrh-closeout` invokes `lrh sessions sync` and a weekly scheduled sync is
  configured (Stage 4; both mandatory per Decision 6).
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

- **Archive-root location.** The Codex durable export default uses the same
  configurable local session archive root as `lrh sessions sync`, with
  date-bucketed `codex/` children. Backup location and encrypted off-machine
  archive policy remain deferred to later archive/sync work.
- **Index-regeneration frequency (non-load-bearing).** Whether
  `project/sessions/` is regenerated on every closeout or only when its
  content would change, to minimize repository churn. The proposal leans
  toward the latter but marks this explicitly non-load-bearing; it does not
  gate this workstream's exit and may be settled informally during Stage 3.

Fork representation was resolved by PR #451 (merged `8fff522`, 2026-08-02):
`session_transcript` stays single-id per thread; fork-spanning work is stitched
in the `project/sessions/` index via `branch` / `writtenBranches[]` / PR
(Decision 4), not represented as a multi-valued pointer. Carried into Stage 1's
index-schema requirement above rather than left as an open item.
