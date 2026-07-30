---
execution_id: 2026_07_29_21_06_52_LRH_CLOSEOUT_AND_PLANNING_SKILL_BUGS
prompt_id: PROMPT(AD_HOC:LRH_CLOSEOUT_AND_PLANNING_SKILL_BUGS)[2026-07-29T21:06:44-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/438
commit: 
agent: claude_app
instruction_source: https://github.com/xenotaur/Taurcode/pull/70 (review comments on the resynced skill copies)
session_transcript: claude-app:3fcab22f-9ebe-4392-bf31-2103fce507f2
created_at: 2026-07-29T21:06:52-04:00
---

# Summary

Fix eight bugs in lrh-closeout, lrh-proposal, lrh-work-item, lrh-workstream,
and lrh-land surfaced by automated review (Copilot + Codex) on Taurcode PR
#70, which resynced these skills downstream: a per-PR (rather than
per-execution-record) session-transcript resolution bug in lrh-closeout, an
idempotence-check-ordering bug in the three planning skills, four instances
of stale `claude-app:<session-id>` placeholder wording, and a missing
`disable-model-invocation: true` on lrh-land.

# Result

TODO: Fill in after review-response/confirm-fixes converge.

# Validation

TODO: List tests or checks run.

# Follow-up

TODO: List deferred work.
