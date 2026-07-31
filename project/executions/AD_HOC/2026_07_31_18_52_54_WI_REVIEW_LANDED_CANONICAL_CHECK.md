---
execution_id: 2026_07_31_18_52_54_WI_REVIEW_LANDED_CANONICAL_CHECK
prompt_id: PROMPT(AD_HOC:WI_REVIEW_LANDED_CANONICAL_CHECK)[2026-07-31T18:09:35+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/447
commit: 8066a28
created_at: 2026-07-31T18:52:54+00:00
agent: claude_app
instruction_source: chat (user request following pros/cons analysis of a self-review-agent proposal)
session_transcript: claude-app:local_d4183878-ad9c-4bb6-80c3-dcd5aa45e103
---

# Summary

Created work item `WI-REVIEW-LANDED-CANONICAL-CHECK` via `/lrh-work-item`,
capturing the "Phase 0" fix identified during a pros/cons discussion of a
proposed self-review-agent stopgap for `/lrh-land`,
`/lrh-review-response`, and `/lrh-confirm-fixes`: forbid ad hoc
`since <timestamp>` filtering of review comments/threads in the
review-landed check, and require the canonical `isResolved`/`commit_id`
data source instead.

# Result

- Ran the prior-art check: no duplicate work item, proposal, or backlog
  entry found. `WI-REVIEW-ROUND-ESCALATION-GATE` touches the same skill
  area but a different problem (retrigger cost-cap ceiling vs. detection
  correctness); cross-linked, not folded in.
- Wrote `project/work_items/proposed/WI-REVIEW-LANDED-CANONICAL-CHECK.md`
  with full frontmatter and body (Summary, Problem/Context with
  duplication/demand search, Scope, Required Changes, Non-Goals,
  Acceptance Criteria, Validation, Risk Notes), grounded in
  `src/lrh/integrations/github/pull_reviews.py:82-178` (confirmed the
  underlying GitHub data fetch is already unfiltered by time) and
  `lrh-confirm-fixes/SKILL.md:119` (confirmed the existing `isResolved`
  filter language this item extends to the other two skills).
- Branched `xenotaur/feat/wi-review-landed-canonical-check` from
  `origin/main` (main was already checked out in a sibling worktree, so
  branched directly from `origin/main` rather than checking main out
  locally).
- Opened PR #447 with the work item.

# Validation

- `lrh validate`: 0 errors, 1 pre-existing warning unrelated to this
  change (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on
  `WS-LRH-ASSISTANTS`).

# Follow-up

- `session_transcript` should be updated to `claude-app:<host-uuid-stem>`
  after this session ends.
- Workstream update to `WS-EXECUTION-FRAMEWORK` was not offered/applied in
  this run (the sibling `WI-REVIEW-ROUND-ESCALATION-GATE` is already
  listed there separately) — revisit whether this item's ID should also be
  added to that workstream's `work_items:` list.
- Implementation of the work item itself (editing the three SKILL.md files
  and their `.claude/` mirrors) is a separate follow-on run.
