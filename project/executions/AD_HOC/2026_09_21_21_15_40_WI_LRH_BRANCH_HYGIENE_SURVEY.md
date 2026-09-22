---
execution_id: 2026_09_21_21_15_40_WI_LRH_BRANCH_HYGIENE_SURVEY
prompt_id: PROMPT(AD_HOC:WI_LRH_BRANCH_HYGIENE_SURVEY)[2026-09-21T21:13:17+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/690
commit: 
created_at: 2026-09-21T21:15:40+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-BRANCH-HYGIENE-SURVEY.md
session_transcript: pending
---

# Summary

Created work item `WI-LRH-BRANCH-HYGIENE-SURVEY`: a report-only `lrh` command
that classifies local git branches and can write reviewable delete commands to
a file. It follows up a session that hand-cleaned 76 local branches and
splits the branch-hygiene slice out of the backlog item at
`project/design/backlog.md:1684-1702`.

# Result

Wrote `project/work_items/proposed/WI-LRH-BRANCH-HYGIENE-SURVEY.md` on branch
`xenotaur/feat/wi-lrh-branch-hygiene-survey` and opened PR #690. Prior-art
check found no duplicate (`WI-SKILLS-LRH-WORK-AUDIT` covers work-item drift,
not branches) and matched the backlog demand entry. `owner` was corrected from
`xenotaur` to `anthony` after `lrh validate` reported `UNKNOWN_OWNER`.

# Validation

`lrh validate`: 0 errors, 0 warnings (after the owner fix).
`lrh work-items readiness WI-LRH-BRANCH-HYGIENE-SURVEY`: ready.

# Follow-up

No workstream linked (left empty by design). The command group and name are an
open design decision for the implementer. `session_transcript: pending` should
be resolved at closeout.
