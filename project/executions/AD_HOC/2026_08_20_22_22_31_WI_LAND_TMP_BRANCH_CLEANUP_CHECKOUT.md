---
execution_id: 2026_08_20_22_22_31_WI_LAND_TMP_BRANCH_CLEANUP_CHECKOUT
prompt_id: PROMPT(AD_HOC:WI_LAND_TMP_BRANCH_CLEANUP_CHECKOUT)[2026-08-20T22:21:21+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/580
commit: 
created_at: 2026-08-20T22:22:31+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LAND-TMP-BRANCH-CLEANUP-CHECKOUT.md
session_transcript: pending
---

# Summary

Created work item `WI-LAND-TMP-BRANCH-CLEANUP-CHECKOUT`, the third of
three skill-content bugs surfaced while triaging Taurcode PR #82 (a
mechanical `lrh skills install --local --force` resync of this project's
own skill package). `/lrh-land` Step 7's main-worktree-lock workaround
deletes `tmp-<slug>` with `git branch -D` while `HEAD` is still checked
out on it — Git always refuses this, right after the closeout commit has
already landed on `main`.

# Result

Wrote
`project/work_items/proposed/WI-LAND-TMP-BRANCH-CLEANUP-CHECKOUT.md`
scoping the fix: check out a branch other than `tmp-<slug>` (the original
PR branch, or a detached `HEAD`) before the delete, in both
`SKILL.md` Step 7 and `references/land-workflow.md`'s `Main-worktree-lock`
rule row. Opened PR #580 from branch
`xenotaur/chore/wi-land-tmp-branch-cleanup-checkout`. This record covers
the planning phase only (work item creation); implementation is a separate
execution record, to be created when the fix is implemented.

# Validation

- `lrh validate` — 0 errors, 0 warnings.

# Follow-up

- Implement the fix described in the work item (edit
  `src/lrh/skills/lrh-land/SKILL.md` Step 7 and
  `references/land-workflow.md`, mirror to `.claude/skills/lrh-land/`).
- Update `session_transcript` from `pending` to the durable session pointer
  once available.
