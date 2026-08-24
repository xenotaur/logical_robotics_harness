---
execution_id: 2026_08_24_06_00_18_WI_LRH_LAND_WORKTREE_CAPTURE_FIX
prompt_id: PROMPT(AD_HOC:WI_LRH_LAND_WORKTREE_CAPTURE_FIX)[2026-08-24T05:58:42+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-LAND-WORKTREE-CAPTURE-FIX.md
session_transcript: claude-app:81eca1c8-36fa-493d-b0e5-08c0501ec1d0
pr: https://github.com/xenotaur/logical_robotics_harness/pull/631
commit: 7dd33d113f1c698bd331ed4185b1e5fcc7f6bf6a
created_at: 2026-08-24T06:00:18+00:00
---

# Summary

Created work item `WI-LRH-LAND-WORKTREE-CAPTURE-FIX`, capturing two real
gaps discovered live during PR #628's own closeout: `/lrh-land`'s
`tmp_branch_parent` capture path fails inside a git worktree checkout
(`.git` is a gitdir-pointer file there, not a directory), and `SKILL.md`
Step 7's illustrative bash snippet is now stale relative to
`land-workflow.md`'s documented capture/cleanup procedure.

# Result

Wrote `project/work_items/proposed/WI-LRH-LAND-WORKTREE-CAPTURE-FIX.md`
(type `operation`, no related workstream, no dependencies). Opened PR #631.

**Correction (review round 1):** the duplication search was originally run
and cited with filesystem `grep -rl`, not the worktree-safe `git grep` this
repo's own convention requires for survey evidence recorded in a committed
artifact -- caught by both `chatgpt-codex-connector` (P1) and
`copilot-pull-request-reviewer` on this PR's first review round. Rerun as
`git grep -nE "git-dir|lrh-tmp-branch-parent|worktree.*capture" --
project/work_items project/design/backlog.md`: matches only within this
work item's own file (self-referential from its own title/body), no prior
independent match. The "no duplicates" conclusion holds; only the cited
command and the WI body's own duplication-search text were wrong, fixed in
the same round. Demand search remains clean -- no existing WI/proposal/
backlog entry requests this fix.

# Validation

- `lrh validate`: 0 errors, 1 pre-existing unrelated warning
  (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` for
  `WS-LRH-CHAIN-DEFAULTS`, unchanged and unrelated to this PR).

# Follow-up

Planning artifact only -- no implementation in this PR. Next: refine to
readiness if needed, then `/lrh-implement WI-LRH-LAND-WORKTREE-CAPTURE-FIX`.
