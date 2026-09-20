---
execution_id: 2026_09_20_02_59_22_DETACHED_HEAD_CLOSEOUT_WORKAROUND_REVIEW
prompt_id: PROMPT(AD_HOC:DETACHED_HEAD_CLOSEOUT_WORKAROUND_REVIEW)[2026-09-20T02:56:09+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/680
commit: 
created_at: 2026-09-20T02:59:22+00:00
---

# Summary

Review-response round for PR #680 (detached-HEAD closeout workflow). Four
Copilot threads (two findings, duplicated across the `src/` and
`.claude/skills/` mirrors): the `HEAD:main` push and `<pr-branch>` checkout
were sequenced before the inlined `/lrh-closeout` commits.

# Result

Both findings valid and present; fixed in `lrh-land/SKILL.md` (Step 7 sketch
and prose) and `land-workflow.md` (Main-worktree-lock row): stay detached
through closeout, push `HEAD:main` after its commit, check out `<pr-branch>`
last. Mirror re-synced. No comments skipped.

# Validation

`scripts/format`, `scripts/lint`, `scripts/test` all pass.

# Follow-up

Threads to be resolved by /lrh-confirm-fixes.
