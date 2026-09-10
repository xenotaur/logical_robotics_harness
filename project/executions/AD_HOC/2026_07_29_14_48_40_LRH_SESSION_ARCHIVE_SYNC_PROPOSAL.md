---
execution_id: 2026_07_29_14_48_40_LRH_SESSION_ARCHIVE_SYNC_PROPOSAL
prompt_id: PROMPT(AD_HOC:LRH_SESSION_ARCHIVE_SYNC_PROPOSAL)[2026-07-29T14:48:33-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/436
commit: 6393c790e92e314b9ddb9f0c0cdf85775746d6e8
created_at: 2026-07-29T14:48:40-04:00
agent: claude_app
instruction_source: 'ad_hoc design session — /lrh-design then /lrh-proposal for a session/PR/execution-record archive-and-sync system, plus PR #436 review response'
session_transcript: claude-app:b7a0de88-bdee-468c-b053-5afbdd7146ad
---

# Summary

Primary record for PR #436: the design and proposal of
`PROP-LRH-SESSION-ARCHIVE-SYNC` (durable local transcript archive, `lrh
sessions` reconciler/discover/link/report, non-authoritative
`project/sessions/` index, both-identifier capture at record creation and
closeout; invariant: no repo-changing agent session is ever lost), together
with the review-response fixes applied to that PR.

# Result

- Ran `/lrh-design` then `/lrh-proposal`; wrote
  `project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md`
  and amended `PROP-LRH-EXECUTION-SESSIONS` Stage 3 to record that session
  discovery (`WI-EXEC-SESSIONS-DISCOVERY` / PR #435) is scoped under the new
  umbrella. Opened PR #436.
- Design incorporated cross-session findings verified against real artifacts:
  the host↔child id mapping lives only in `/export` `metadata.json` and live
  env vars (raw JSONL cannot rebuild it); the fork-vs-resume identity model;
  ~30-day transcript retention; dangling-pointer decay 28%→14% (2026-07-23 →
  07-29).
- Addressed five review comments (Copilot ×1, Codex ×4): (1) Stage-3 heading
  now consistent with its body; (2) P1 — the captured child-id alias is given
  a durable home by introducing a minimal `project/sessions/` index in Stage 1
  (no schema change); (3) P1 — archive re-mirrors growing transcripts
  atomically instead of "never rewritten"; (4) P2 — weekly scheduled sync
  stated as required, only the `SessionEnd` hook optional; (5) P2 — corrected
  `WI-EXEC-SESSIONS-DOCS`/`-SCHEMA` from "proposed" to their real `resolved`
  status.

# Validation

- `lrh validate` — 0 errors (1 pre-existing unrelated warning:
  `WS-LRH-ASSISTANTS` has no actionable leaf).
- PR #436 CI at open: workflow-files, coverage, installed-wheel-smoke, lint,
  tests all passed.

# Follow-up

- After merge: `/lrh-workstream` to group the four implementation stages (held
  by user until the proposal lands).
- Reconcile PR #435 (`WI-EXEC-SESSIONS-DISCOVERY`, discover/link) against the
  adopted design.
- Archive-root location remains an open design-discussion question in the
  proposal.
