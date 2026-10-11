---
execution_id: 2026_10_10_18_25_36_WI_SERVE_PROJECT_SCOPED_WORK_ITEM_ROUTES_REVIEW
prompt_id: PROMPT(AD_HOC:WI_SERVE_PROJECT_SCOPED_WORK_ITEM_ROUTES_REVIEW)[2026-10-10T18:25:19+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_10_10_18_06_29_WI_SERVE_PROJECT_SCOPED_WORK_ITEM_ROUTES_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/818
commit: 08bf5cfbeda32c1edf3d172248f2080798ad83f1
created_at: 2026-10-10T18:25:36+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/818
session_transcript: claude-app:c94e499e-da6e-4e3f-a979-5876278e9f67
---
# Summary

Review-response round 2 for PR 818, run inline from `/lrh-land` Step 5 after
the stop-work gate. The owner chose "fix now" for the three low-severity
spec gaps that the PR-mode self-review of `31ff61a2` raised
(`2026_10_10_18_09_52_WI_SERVE_PROJECT_SCOPED_WORK_ITEM_ROUTES_CONFIRM_SELFREVIEW`).
These findings came from the self-review, not from GitHub threads. The
owner's "fix now" answer named the three changes and served as this round's
confirm gate. The slug check matched round 1's `in_progress` `_REVIEW`
record, which this same run wrote earlier, so the same-land-run
continuation carve-out applies.

# Result

Fix commit `5f201455513b2771a30e625d01b872dec8b3ab7c`.

1. **HEAD acceptance criteria aligned.** Frontmatter and body now both
   require:
   - HEAD on the work-item routes matches GET's status and content type,
     including 404 and 409;
   - HEAD on the dependency-map routes returns 409 for a missing bound
     checkout.
2. **The missing-path message reaches HTML.** Required Change 2 now updates
   `render_project_selector_error_page` to show `error.message` with the
   bind command, in place of its fixed sentence. Both acceptance lists and
   the test list require the missing path to be named on the HTML page and
   in the JSON.
3. **The existence check tests the repo path.** Required Change 2 now tests
   `selection.resolved_repo_path`, not `resolved_project_path`, and explains
   why. A new Non-Goal leaves a repo without its project directory at
   today's behavior.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items readiness WI-SERVE-PROJECT-SCOPED-WORK-ITEM-ROUTES`:
  prompt-ready.
- `scripts/format --check --diff`: 295 files unchanged.
- `scripts/lint`: passed.
- `scripts/test`: 2200 tests, OK.

All runs used the `LrhLocalAgent` env with `PYTHONPATH=src`.

# Follow-up

- Re-run confirm-fixes and a fresh substitute review on the new HEAD.
