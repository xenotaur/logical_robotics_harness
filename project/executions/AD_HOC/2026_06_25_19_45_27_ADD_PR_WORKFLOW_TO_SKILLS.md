---
execution_id: 2026_06_25_19_45_27_ADD_PR_WORKFLOW_TO_SKILLS
prompt_id: PROMPT(AD_HOC:ADD_PR_WORKFLOW_TO_SKILLS)[2026-06-25T19:36:53-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/327
commit: 88f04bc
agent: claude_app
instruction_source: ad_hoc conversation — gap identified during /lrh-create-skill lrh-design session
session_transcript: claude-app:6ca47ac2-78b7-46b5-9ca4-1e80a8720b8b
created_at: 2026-06-25T19:45:27-04:00
---

# Summary

Add feature-branch + PR workflow to /lrh-create-skill and /lrh-work-item.
Both skills wrote files directly to the current branch. They now create a
branch from main before writing and open a PR after validation, matching
/lrh-implement. /lrh-create-skill also gains the src/lrh/skills/ copy step.

# Result

- Added Step 5 (create branch) and Step 9 (commit+PR) to /lrh-create-skill;
  renumbered old Steps 5-7 to 6-8+10; added src copy to Step 6; updated
  quality checklist; removed "Does not create src/lrh/skills/ copies" from
  What This Skill Does Not Do
- Added Step 5 (create branch) and Step 8 (commit+PR) to /lrh-work-item;
  renumbered old Steps 5-7 to 6-7+9; updated quality checklist; fixed
  step reference in What This Skill Does Not Do
- Synced all four files (.claude/ and src/ copies) byte-for-byte

# Validation

scripts/format --check --diff — 173 files unchanged
scripts/lint — all checks passed
scripts/test — 679 tests OK
lrh validate — 0 errors, 0 warnings
diff -r src/lrh/skills/lrh-create-skill/ .claude/skills/lrh-create-skill/ — in-sync
diff -r src/lrh/skills/lrh-work-item/ .claude/skills/lrh-work-item/ — in-sync

# Follow-up

- Update session_transcript from pending to claude-app:<session-id> after session ends
- Dismiss background chip task_386897b5 once this PR lands
