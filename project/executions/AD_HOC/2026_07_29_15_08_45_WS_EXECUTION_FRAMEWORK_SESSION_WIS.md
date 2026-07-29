---
execution_id: 2026_07_29_15_08_45_WS_EXECUTION_FRAMEWORK_SESSION_WIS
prompt_id: PROMPT(AD_HOC:WS_EXECUTION_FRAMEWORK_SESSION_WIS)[2026-07-29T15:07:15-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/437
commit: 6d73670
created_at: 2026-07-29T15:08:45-04:00
agent: claude_app
instruction_source: ad_hoc conversation — reconcile PR #435 against the landed PROP-LRH-SESSION-ARCHIVE-SYNC; salvage the workstream hygiene half
session_transcript: claude-app:f1e9c968-f61d-4618-979c-29f8b08bfb0c
---

# Summary

Reconcile PR #435 against the newly-landed `PROP-LRH-SESSION-ARCHIVE-SYNC`
(PR #436, merged `6393c79`): close #435 as superseded, and reland its
independently-correct workstream hygiene half as PR #437.

# Result

**Reconciliation finding.** PR #435 (`WI-EXEC-SESSIONS-DISCOVERY`) was written
before the archive/export-harvest design existed, and four of its five
acceptance criteria no longer hold under the adopted proposal:

- `discover` labelling ids as child-only — **superseded** (harvest lets
  `discover` surface the host id).
- `link` never promoting a bare child id — **partly superseded** (harvest makes
  child→host resolution authoritative).
- Both commands local-filesystem-only with no session-listing dependency —
  **directly conflicts** with adopted Decision 1's recovery heuristic, which
  joins the session listing on branch/PR.
- `discover`'s scan criterion — **incomplete** (no archive awareness; misses
  in-file child ids).

Plus structural mismatches: `related_design` pointed only at the superseded
Stage 3 framing, `related_workstreams` named the wrong workstream now that a
dedicated governing one is being created, and the `…-DISCOVERY` id no longer
matches a Stage 2 scope covering `sync` and the archive layout. Rewriting id,
workstream, links, scope, non-goals and 4/5 criteria amounts to a new
stage-aligned WI, so #435 was **closed unmerged** with the reconciliation and
carry-forward items recorded in a closing comment.

**Salvaged half (this PR).** `WI-EXEC-SESSIONS-DOCS`,
`WI-EXEC-SESSIONS-SCHEMA`, and `WI-CLOSEOUT-SESSION-SOURCING` are all resolved
and all declare `related_workstreams: WS-EXECUTION-FRAMEWORK`, but none was
listed in that workstream's `work_items:`. Added all three. Deliberately did
**not** carry over #435's `WI-EXEC-SESSIONS-DISCOVERY` entry, since that work
item no longer exists.

**Carried forward to the new workstream's future WIs** (recorded on the #435
closing comment, not in this PR): the permissive-with-a-gate `forbidden_actions`
form for `/lrh-closeout` edits; append-safety for growing transcripts; and
complete child-id alias collection from in-file `sessionId` values. The latter
two were review findings raised on PR #436 and belong as Stage 2 acceptance
criteria.

# Validation

- `lrh validate` — 0 errors, 1 pre-existing unrelated warning
  (`WS-LRH-ASSISTANTS` no actionable leaf)
- `lrh work-items validate` — no warnings referencing the three WIs
- Confirmed all three files exist under `project/work_items/resolved/` with
  `status: resolved`, so the added references resolve

# Follow-up

- The governing workstream for `PROP-LRH-SESSION-ARCHIVE-SYNC` is still to be
  created; it should file stage-aligned work items rather than reusing the
  closed `WI-EXEC-SESSIONS-DISCOVERY` id.
- **`WI-EXEC-SESSIONS-DISCOVERY` is retired for good** (human decision,
  2026-07-29). The id names a scope that no longer exists — `discover`/`link`
  are now one leaf of Stage 2 in `PROP-LRH-SESSION-ARCHIVE-SYNC`, not a
  standalone work item — and reusing a closed work item's id would make the
  history ambiguous to read later. No work item file was ever merged under
  that id; it exists only in closed PR #435 and in the amended Stage 3 note
  in `PROP-LRH-EXECUTION-SESSIONS`, both of which remain accurate as history.
