---
execution_id: 2026_08_20_04_47_48_WI_SELF_REVIEW_UNTRACKED_FILE_DIFF
prompt_id: PROMPT(AD_HOC:WI_SELF_REVIEW_UNTRACKED_FILE_DIFF)[2026-08-20T04:46:46+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/575
commit: 0900ff4f8c814b85197c3bca711a4ada7097bb1c
created_at: 2026-08-20T04:47:48+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SELF-REVIEW-UNTRACKED-FILE-DIFF.md
session_transcript: claude-app:c02da21d-4a23-4315-857f-0829e0483667
---

# Summary

Created work item `WI-SELF-REVIEW-UNTRACKED-FILE-DIFF`, the second of three
skill-content bugs surfaced while triaging Taurcode PR #82 (a mechanical
`lrh skills install --local --force` resync of this project's own skill
package). `/lrh-self-review` Step 1 diff-mode uses `git diff main`, which
never includes untracked files — if `/lrh-implement` Step 6 only creates
new files with no tracked-file modifications, the diff is empty and
review is silently skipped.

# Result

Wrote
`project/work_items/proposed/WI-SELF-REVIEW-UNTRACKED-FILE-DIFF.md`
scoping the fix: stage new files with intent-to-add (`git add -N`) before
computing the diff in Step 1's diff-mode block, preserving the existing
two-dot-vs-three-dot rationale unchanged. Opened PR #575 from branch
`xenotaur/chore/wi-self-review-untracked-file-diff`. This record covers
the planning phase only (work item creation); implementation is a separate
execution record, to be created when the fix is implemented.

# Validation

- `lrh validate` — 0 errors, 0 warnings.

# Follow-up

- Implement the fix described in the work item (edit
  `src/lrh/skills/lrh-self-review/SKILL.md` Step 1 and mirror to
  `.claude/skills/lrh-self-review/SKILL.md`).
- Update `session_transcript` from `pending` to the durable session pointer
  once available.
