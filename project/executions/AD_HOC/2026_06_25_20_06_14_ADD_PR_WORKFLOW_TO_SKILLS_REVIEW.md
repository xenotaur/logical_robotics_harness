---
execution_id: 2026_06_25_20_06_14_ADD_PR_WORKFLOW_TO_SKILLS_REVIEW
prompt_id: PROMPT(AD_HOC:ADD_PR_WORKFLOW_TO_SKILLS_REVIEW)[2026-06-25T19:53:15-04:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_06_25_19_45_27_ADD_PR_WORKFLOW_TO_SKILLS
pr: https://github.com/xenotaur/logical_robotics_harness/pull/327
commit: 8ffed99
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/327
session_transcript: claude-app:6ca47ac2-78b7-46b5-9ca4-1e80a8720b8b
created_at: 2026-06-25T20:06:14-04:00
---

# Summary

Address review feedback on PR #327 (Add branch+PR workflow to /lrh-create-skill
and /lrh-work-item). Three issues fixed: src/ ordering in lrh-create-skill Step 6,
stale-check re-verification in both skills' Step 6, and workstream commit gap in
lrh-work-item Step 9.

# Result

Fixed all 3 reviewer issues:

1. **src/ ordering (lrh-create-skill Step 6):** Rewrote to create
   `src/lrh/skills/<name>/` first (authoritative per CONTRIBUTING.md lines
   220-222), then copy to `.claude/skills/<name>/`. Original PR wrote
   `.claude/` first.

2. **Stale duplicate check (both skills Step 6):** Added re-verification at the
   start of Step 6 in both skills — the Step 1 check may be stale if main
   advanced between session start and write time. lrh-create-skill checks both
   `src/` and `.claude/` paths; lrh-work-item re-runs the `find` for the WI file.

3. **Workstream commit gap (lrh-work-item Step 9):** Added explicit
   `lrh validate && git add && git commit && git push` clause after workstream
   edit approval — prevents the approved update from being left uncommitted on
   the PR branch.

Synced all four files (.claude/ and src/ copies) byte-for-byte.

# Validation

scripts/format --check --diff — 173 files unchanged
scripts/lint — all checks passed
scripts/test — 679 tests OK
lrh validate — 0 errors, 0 warnings
diff -r src/lrh/skills/lrh-create-skill/ .claude/skills/lrh-create-skill/ — in-sync
diff -r src/lrh/skills/lrh-work-item/ .claude/skills/lrh-work-item/ — in-sync

# Follow-up

- Update session_transcript from pending to claude-app:<session-id> after session ends
