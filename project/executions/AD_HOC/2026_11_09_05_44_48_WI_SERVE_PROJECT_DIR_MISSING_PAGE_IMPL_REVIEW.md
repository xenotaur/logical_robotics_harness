---
execution_id: 2026_11_09_05_44_48_WI_SERVE_PROJECT_DIR_MISSING_PAGE_IMPL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_SERVE_PROJECT_DIR_MISSING_PAGE_IMPL_REVIEW)[2026-11-09T05:44:46+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_11_09_05_08_14_WI_SERVE_PROJECT_DIR_MISSING_PAGE_IMPL_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/850
commit:
created_at: 2026-11-09T05:44:48+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/850
session_transcript: pending
---
# Summary

Review-response round 3 for PR 850. The owner chose option 1 at the second
stop-work decision: fix the parts this PR owns from the PR-mode self-review
round 2 of `8a498669`, then merge. For the rest of this run, observations a
reviewer itself classifies as "not a defect" go into the closeout note as
follow-ups instead of blocking the merge.

The same-land-run carve-out covers the round-2 `in_progress` `_REVIEW`
match. The owner's option-1 answer served as this round's confirm gate.

# Result

Fix commit: `4e30eae5993e4bad5460e0980853f07f21c1b714`.

1. **Item 2, in this PR's code: fixed.** `_no_project_directory_error` now
   treats a symlink at `<repo>/project` that resolves outside the checkout
   as blocking. Meta will not resolve a project directory outside the
   repository, so neither `lrh project init` nor a repoint to `project`
   would clear the 409.
   - Only the `--project-dir DIR` repoint is offered.
   - The message says "a symlink that leads outside the checkout is there;
     move it aside".
   - The test gains an `escaping` case.
2. **Item 1, docs: narrowed.**
   - The blocking-symlink bullet now covers only broken or escaping links.
   - A new bullet says an explicit `project_dir` that resolves outside the
     checkout is still reported as having no local checkout. This is
     pre-existing Meta behavior.
   - The "existing `<repo>/project` directory" sentence now says "inside the
     checkout".
   - The underlying resolution behavior is out of scope and is recorded as
     a closeout follow-up.
3. **Item 3, a wording nit the reviewer marked "not a defect".** Recorded as
   a closeout follow-up; not changed.

# Validation

All runs used the `LrhLocalAgent` env with `PYTHONPATH=src`.

- `scripts/format --check --diff`: exit 0.
- `scripts/lint`: exit 0.
- `scripts/test`: 2369 tests, OK.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- Run confirm-fixes round 3 and a substitute review on the new HEAD.
