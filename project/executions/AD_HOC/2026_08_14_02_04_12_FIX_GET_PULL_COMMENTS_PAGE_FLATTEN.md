---
execution_id: 2026_08_14_02_04_12_FIX_GET_PULL_COMMENTS_PAGE_FLATTEN
prompt_id: PROMPT(AD_HOC:FIX_GET_PULL_COMMENTS_PAGE_FLATTEN)[2026-08-14T01:59:14+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/555
commit: b906baa2
created_at: 2026-08-14T02:04:12+00:00
agent: claude_app
instruction_source: ad_hoc conversation — Codex-review-caught follow-up bug flagged during PR #553 (WI-REVIEW-RESPONSE-ISSUE-COMMENTS), out of scope for that PR's non-goals
session_transcript: pending
---

# Summary

`get_pull_comments()` in `src/lrh/integrations/github/pull_reviews.py`
stored the raw `gh api --paginate --slurp` payload directly as
`review_comments`/`issue_comments` without flattening pages. `--slurp`
wraps each page in an outer array, so the payload is a list of pages
(each page itself a list of comments), not a flat list.
`format_comments()` in `src/lrh/integrations/github/formatters.py`
(used by `lrh github comments <pr-url>`) then did `len()` on that
unflattened value, silently reporting the page count instead of the
comment count for any PR with review/issue comments. This is the same
bug just fixed in `get_pull_issue_comments()` on PR #553 (commit
`5ac74dc8`, not yet merged to main), whose work item explicitly
excluded touching `get_pull_comments()`/`format_comments()`.

# Result

Added a shared `_flatten_paginated_pages()` helper in
`pull_reviews.py` and used it for both the `review_comments` and
`issue_comments` fetches in `get_pull_comments()`. Fixed the existing
`test_get_pull_comments_uses_paginate` mock (it previously mocked a
flat list, not the correct nested-page shape) and added
`test_get_pull_comments_flattens_paginated_pages`, asserting flattened
comment lists and `format_comments()`'s resulting counts against
multi-page mocks. Opened PR #555 against `main`.

Note: `/lrh-self-review` is now gated to explicit user invocation only
(`disable-model-invocation`) and could not be run as this skill's
usual Step 7.5 pre-push pass.

# Validation

- `scripts/version tools` — confirmed tool versions; found Black/Ruff
  pins had drifted (25.11.0/0.15.0 vs required 26.3.1/0.15.12) and
  re-ran `scripts/develop` to realign before continuing
- `scripts/format --check --diff` — 196 files unchanged (after one
  reformat)
- `scripts/lint` — all checks passed
- `PYTHONPATH="$(pwd)/src" scripts/test` — Ran 1087 tests, OK
- `lrh validate` — 0 errors, 1 pre-existing unrelated warning
  (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on
  `WS-SESSION-ARCHIVE-SYNC.md`)

# Follow-up

- Wait for reviewer/bot comments on PR #555 and address via
  `/lrh-review-response`, then `/lrh-confirm-fixes` before merge.
- After merge, run `/lrh-closeout` to land this execution record.
- If PR #553 merges first and `get_pull_issue_comments()` lands with
  its own flattening helper, this PR's `_flatten_paginated_pages()`
  could later be unified with it — not done here since PR #553 was
  still open at the time of this fix.
