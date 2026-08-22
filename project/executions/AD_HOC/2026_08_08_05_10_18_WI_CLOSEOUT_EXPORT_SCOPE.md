---
execution_id: 2026_08_08_05_10_18_WI_CLOSEOUT_EXPORT_SCOPE
prompt_id: PROMPT(AD_HOC:WI_CLOSEOUT_EXPORT_SCOPE)[2026-08-08T05:08:57+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/519
commit: 
created_at: 2026-08-08T05:10:18+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-CLOSEOUT-EXPORT-SCOPE.md
session_transcript: pending
---

# Summary

Created work item `WI-CLOSEOUT-EXPORT-SCOPE`, designed via `/lrh-design`
this session in response to closing out PR #516: `/lrh-closeout` Step 8
offers `/export` unconditionally even when its own "Pending offers" list
(computed a few lines earlier in the same step) is non-empty — an internal
inconsistency, since `/export` implies the session's work is finished.

# Result

Wrote `project/work_items/proposed/WI-CLOSEOUT-EXPORT-SCOPE.md` scoping the
fix: gate the Step 8 `/export` offer on the Pending-offers list being empty,
and document `/lrh-closeout`'s single-PR scoping limitation (pointing to
`WI-SKILLS-LRH-WORK-REMAINS` for the broader session-wide gap this narrower
fix does not close). Opened PR #519 from branch
`xenotaur/chore/wi-closeout-export-scope`. This record covers the planning
artifact only — implementation of the fix itself is a follow-on
`/lrh-implement` run against this WI.

# Validation

- `lrh validate`: 0 errors, 1 pre-existing unrelated warning
  (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on `WS-SESSION-ARCHIVE-SYNC`)

# Follow-up

- Implement `WI-CLOSEOUT-EXPORT-SCOPE` via `/lrh-implement`
- File the deferred companion work item (`depends_on:
  [WI-SKILLS-LRH-WORK-REMAINS]`) recommending Step 8 chain to
  `/lrh-work-remains` before `/export` once that skill ships
- `session_transcript: pending` — update to `claude-app:<host-uuid-stem>`
  after this session ends
