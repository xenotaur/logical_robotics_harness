---
execution_id: 2026_11_09_05_08_14_WI_SERVE_PROJECT_DIR_MISSING_PAGE_IMPL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_SERVE_PROJECT_DIR_MISSING_PAGE_IMPL_REVIEW)[2026-11-09T05:07:56+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_10_24_21_16_07_WI_SERVE_PROJECT_DIR_MISSING_PAGE_IMPL_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/850
commit:
created_at: 2026-11-09T05:08:14+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/850
session_transcript: pending
---
# Summary

Review-response round 2 for PR 850, run inline from `/lrh-land` Step 5
inside `/lrh-execute`. The PR-mode self-review of `7e6a8172` made three
observations it called "not defects". One of them was a wording slip in
text this PR wrote, and at the stop-work decision the owner chose "fix the
wording now". That answer served as this round's confirm gate.

The finding came from the self-review, not from a GitHub thread. The slug
check matched round 1's `in_progress` `_REVIEW` record, which this same land
run wrote, so the same-land-run continuation carve-out applies.

# Result

Fix commit: `d7971a298c00cf6fd7385da17b655ba1bf3cd8a0`.

- Before: when a broken symlink, not a regular file, sat at
  `<repo>/project`, the 409 message still said "while a file is there" and
  "move the file aside".
- Now `_no_project_directory_error` names what is in the way: "while a
  symlink is there" or "while a file is there", followed by "move it aside".
- The docstring and the "Project selectors" docs bullet now match this
  wording. That also reflows an awkward docs line break.
- The test asserts the exact noun for each case: `dangling`, `occupied`,
  and `blocked`.
- The other two self-review observations need no change. One concerns the
  resolved target named for an explicit dangling `project`; the other is
  the `normpath` classification. The suggested commands are correct in
  both cases.

# Validation

All runs used the `LrhLocalAgent` env with `PYTHONPATH=src`. `lrh` was
confirmed to import from this worktree.

- `scripts/format --check --diff` exit 0
- `scripts/lint` exit 0
- `scripts/test`: 2369 tests, OK
- `lrh validate`: 0 errors, 0 warnings

# Follow-up

- Run confirm-fixes round 2 and a fresh substitute review on the new HEAD.
