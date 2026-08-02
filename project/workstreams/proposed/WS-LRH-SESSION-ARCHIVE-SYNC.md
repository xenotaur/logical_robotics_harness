---
id: WS-LRH-SESSION-ARCHIVE-SYNC
kind: planning_node
title: LRH Session Archive and Sync
status: proposed
stage: designed
origin: design_review
summary: Deliver a durable local archive for agent session transcripts and the tooling that keeps it reconciled with the LRH control plane, per PROP-LRH-SESSION-ARCHIVE-SYNC's staged plan — closing the dangling-pointer gap in session_transcript resolution.
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_design:
  - project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md
  - project/design/proposals/proposed/lrh-execution-sessions/00_proposal.md
  - project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md
  - project/workstreams/proposed/WS-EXECUTION-FRAMEWORK.md
work_items: []
exit_criteria:
  - PROP-LRH-SESSION-ARCHIVE-SYNC is adopted
  - Stage 1 (both-identifier capture + minimal project/sessions/ index) lands, closing the gap for all future execution records
  - Stage 2 (archive store + lrh sessions sync/discover/link) lands with unit tests over parsing, change detection, and idempotency
  - Stage 3 (index enrichment + lrh sessions report) lands and the current dangling pointers get a one-time recovery attempt
  - Stage 4 (weekly scheduled sync, required; SessionEnd hook, optional) lands, closing the retention-window gap for sessions that never reach closeout
  - lrh sessions report shows 0 unexplained dangling pointers for sessions created after Stage 1 lands
---

# WS-LRH-SESSION-ARCHIVE-SYNC — LRH Session Archive and Sync

## Purpose

Deliver the durable local session-transcript archive and reconciler defined by
[`PROP-LRH-SESSION-ARCHIVE-SYNC`](../../design/proposals/proposed/lrh-session-archive-sync/00_proposal.md):
an `lrh sessions` command family (`sync`, `discover`, `link`, `report`), a
private local archive store, a committed non-authoritative `project/sessions/`
index, and both-identifier capture at record creation and closeout. The
governing invariant is that no agent session that changed this repository is
ever lost. This workstream exists now because the gap is measured and
decaying — session-pointer resolution by name dropped from 28% to 14% between
2026-07-23 and 2026-07-29 as Claude Code's ~30-day JSONL retention prunes
unresolved sessions.

This workstream fulfils the deferred Stage 3 of `PROP-LRH-EXECUTION-SESSIONS`
as a strict superset, per that proposal's own Prior Art Check, and stays
consistent with `PROP-LRH-CONVERSATIONS-STORAGE-INTEROP`'s storage-class
vocabulary.

## Scope

- Adopt `PROP-LRH-SESSION-ARCHIVE-SYNC` and resolve its one open design
  question (archive root location) as part of, or ahead of, Stage 1
- Implement the four staged deliverables (capture, archive/reconciler, index
  enrichment/report, scheduling) as separate work items in delivery order
- Wire `/lrh-closeout` and `/lrh-implement` to the new capture path
- Reconcile with `PROP-LRH-EXECUTION-SESSIONS` Stage 3 (mark it fulfilled)

## Prior Art Check

### Duplication search
- In-repo: No existing implementation. `src/lrh/conversations/` (ChatGPT PDF
  import + sensitivity scanner) is the earlier era's capture path, related but
  not overlapping. `lrh sessions discover`/`link` were previously scoped as
  `WI-EXEC-SESSIONS-DISCOVERY` (PR #435) but that PR was **closed unmerged**
  on 2026-07-29, superseded by this proposal — see "Carried forward from PR
  #435" below for what must not be lost from that closure.
- Sibling repos: None identified (per the proposal's own check).
- External libraries: None identified for adoption as a whole (per the
  proposal's own check); general-purpose sync/backup tool semantics are
  referenced, not depended upon.
- Recommendation: **Proceed.**

### Demand search
- Work items: None currently filed under this design (PR #435's WI was
  closed rather than retrofitted — its ID, workstream link, and 4/5
  acceptance criteria no longer matched the adopted design).
- Proposals: `PROP-LRH-EXECUTION-SESSIONS` (`implementation_status: partial`)
  — its deferred Stage 3 is fulfilled by this workstream, not duplicated.
- Backlog: No matching entries.
- Recommendation: **No action** beyond the Stage 1 amendment to
  `PROP-LRH-EXECUTION-SESSIONS` the proposal itself calls for.

## Carried forward from PR #435's closure

Three findings must not be lost when Stage 1/2 work items are filed:

1. **Permissive-with-a-gate `forbidden_actions`.** Don't hard-block
   `modify_lrh_closeout_skill` — Stage 1 modifies `/lrh-closeout` by design.
   Use a gated form (ask for explicit approval before going beyond scope).
2. **Append-safety for growing transcripts** (live review finding: a
   transcript measured 6.4M → 6.8M mid-session). `sync` must re-copy a
   session's raw file while the session is still live, never "copy once" —
   this is already Decision 2's re-mirror behavior in the adopted design, but
   must be an explicit acceptance criterion on the Stage 2 work item.
3. **Complete child-id aliases** (live review finding: a file named
   `f1e9c968…` contained a second `sessionId`, `aff3efd3…` — 1629 lines —
   appearing in no filename anywhere). Alias collection must scan line-level
   `sessionId` values inside each JSONL, not just filename stems; must be an
   explicit acceptance criterion on the Stage 2 work item.

## Work Items

None filed yet. Per the proposal's Implementation Plan, work items should be
filed one stage at a time, in this order:

- **Stage 1 — Both-identifier capture.** Extend `/lrh-implement` record
  creation and `/lrh-closeout` to capture both `CLAUDE_CODE_HOST_SESSION_ID`
  and `CLAUDE_CODE_SESSION_ID`; introduce the minimal `project/sessions/`
  index. No schema change. Lands standalone and first.
- **Stage 2 — Archive and reconciler.** Archive layout, `lrh sessions sync`
  (raw mirror + export-metadata harvest), `discover`, `link`. Carries forward
  the three items above as acceptance criteria.
- **Stage 3 — Index enrichment and report.** Era-general keys, fork
  stitching, `lrh sessions report`, one-time recovery attempt for current
  dangling pointers.
- **Stage 4 — Scheduling.** Required weekly `lrh sessions sync`; optional
  `SessionEnd` hook.

## Non-Goals

- Does not commit session transcripts, in any form, to this repository.
- Does not copy `/export` logs or transcript bodies into any committed or
  shareable artifact — only `metadata.json` identity fields are harvested.
- Does not implement redaction, sanitization, or a public-export pipeline.
- Does not build the encrypted off-machine archive tier now (permitted
  later, not designed out).
- Does not change the execution-record schema or `session_transcript`
  pointer format (both already landed in PR #409).
- Does not supersede `PROP-LRH-CONVERSATIONS-STORAGE-INTEROP` or
  `PROP-LRH-EXECUTION-SESSIONS`.
- Does not retroactively recover sessions with no surviving transcript or
  export — those stay honestly recorded as lost.

## Open Questions

- **Archive root location** — deferred to a design discussion ahead of or
  during Stage 1; candidate default `~/Archives/lrh-sessions/`, must be
  configurable regardless.
- Whether `project/sessions/` regenerates every closeout or only on content
  change (leaning toward the latter; not load-bearing per the proposal).
