---
execution_id: 2026_08_08_19_26_28_WI_REVIEW_RESPONSE_ISSUE_COMMENTS
prompt_id: PROMPT(AD_HOC:WI_REVIEW_RESPONSE_ISSUE_COMMENTS)[2026-08-08T19:24:34+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/527
commit: 6b6539e
created_at: 2026-08-08T19:26:28+00:00
agent: claude_app
instruction_source: user-authored bug report (LCATS repo WI-ASSESS-0031 review-response loop finding)
session_transcript: claude-app:860a6ba4-730e-4113-80e7-290d85a766f1
---

# Summary

Created WI-REVIEW-RESPONSE-ISSUE-COMMENTS to track a confirmed gap:
`lrh request review_response` fetches and surfaces only formal GitHub
`reviewThreads`, never PR issue comments, even though
`pull_reviews.get_pull_comments()` already fetches `issue_comments` for
other call sites. This can silently drop real findings or clean-pass
confirmations that a reviewer bot posts as a plain issue comment instead
of a review thread.

# Result

Verified every claim in the source report directly against this repo's
current code (not memory or the originating repo) before writing the
work item:

- Confirmed `request_service.py:125`'s `generate_request()` calls only
  `get_pull_review_threads()`; `get_pull_comments()` is invoked
  elsewhere (`cli/github.py:58`) but never reaches `review_response`.
- Confirmed `review_response.md` interpolates only `{{UNRESOLVED_THREADS}}`
  with no issue-comment equivalent.
- Confirmed the `request_service.py:148-156` early-return gate checks
  only unresolved-thread state, not issue comments.
- Checked and ruled out the suspected "review body as findings" gap:
  the only `.get("body")` read in `formatters.py` is a thread comment's
  body, not a review's top-level body — not reachable in the
  `review_response` path, so no fix scoped for it.
- Ran prior-art duplication and demand searches: no existing
  implementation or open work item/proposal/backlog entry covers issue
  comments specifically (a related but distinct backlog entry exists for
  a different `review_response` gap — outdated-but-unresolved thread
  filtering, already partly addressed by resolved
  `WI-REVIEW-RESPONSE-INCLUDE-THREAD`).

Wrote `project/work_items/proposed/WI-REVIEW-RESPONSE-ISSUE-COMMENTS.md`
with full frontmatter and body (Summary, Problem/Context with prior-art
verdicts, Scope, Required Changes, Non-Goals, Acceptance Criteria,
Validation, Risk Notes). Opened PR #527.

# Validation

- `lrh validate` reported 0 errors (1 pre-existing, unrelated warning:
  `WS-SESSION-ARCHIVE-SYNC` has no actionable leaf).

# Follow-up

- This work item only files the planning artifact; the actual
  `review_response` fix (fetch wiring, formatter, template variable,
  early-return gate change, skill propagation) is not yet implemented.
- Landing this PR via `/lrh-land`.
