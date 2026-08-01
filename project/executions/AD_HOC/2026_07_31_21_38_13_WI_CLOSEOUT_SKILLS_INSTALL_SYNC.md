---
execution_id: 2026_07_31_21_38_13_WI_CLOSEOUT_SKILLS_INSTALL_SYNC
prompt_id: PROMPT(AD_HOC:WI_CLOSEOUT_SKILLS_INSTALL_SYNC)[2026-07-31T21:36:42-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/454
commit: 
created_at: 2026-07-31T21:38:13-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-CLOSEOUT-SKILLS-INSTALL-SYNC.md
session_transcript: claude-app:local_20d16dd9-a465-4d31-b39f-280db14488ef
---

# Summary

While diagnosing why `~/.claude/skills/lrh-confirm-fixes/SKILL.md` was
missing PR #445's round-cap-gate mechanism mid-`/lrh-land` run on PR #452,
root-caused that `/lrh-closeout` never runs `lrh skills install` after a
PR edits an existing skill, and filed `WI-CLOSEOUT-SKILLS-INSTALL-SYNC` to
close that gap.

# Result

- Diagnosed the immediate staleness by diffing the global copy against
  `origin/main`'s `src/lrh/skills/lrh-confirm-fixes/` directly (the shared
  primary checkout was occupied by another session on an unrelated
  branch, so it was not used for this).
- Found the same drift in 5 more skills (`lrh-land`, `lrh-proposal`,
  `lrh-review-response`, `lrh-work-item`, `lrh-workstream`) and manually
  reinstalled all 6 by direct file copy from `src/lrh/skills/` as an
  immediate stopgap (outside this PR — no repo files changed by that
  step).
- Wrote `project/work_items/proposed/WI-CLOSEOUT-SKILLS-INSTALL-SYNC.md`
  describing the structural fix: `/lrh-closeout` should detect when the
  closed-out PR touched `.claude/skills/` or `src/lrh/skills/` and either
  run `lrh skills install` or explicitly prompt the human, rather than
  leaving the global copy silently stale.
- Opened PR #454 with the work item.

# Validation

- `lrh validate`: 0 errors, 1 pre-existing unrelated warning
  (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on
  `WS-LRH-ASSISTANTS`).

# Follow-up

- Implementation of the fix described in `WI-CLOSEOUT-SKILLS-INSTALL-SYNC`
  is not part of this PR — this record covers the work-item creation only.
- `session_transcript` above uses the host session id; update if this
  turns out to need the export-derived host↔child mapping instead.
