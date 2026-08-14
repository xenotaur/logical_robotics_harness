---
execution_id: 2026_08_14_01_34_13_WI_REVIEW_RESPONSE_ISSUE_COMMENTS
prompt_id: PROMPT(WI-REVIEW-RESPONSE-ISSUE-COMMENTS:WI_REVIEW_RESPONSE_ISSUE_COMMENTS)[2026-08-13T07:02:40+00:00]
work_item: WI-REVIEW-RESPONSE-ISSUE-COMMENTS
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/553
commit: 20c30b7d1b135dc1f826929836c88a2761683182
created_at: 2026-08-14T01:34:13+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-REVIEW-RESPONSE-ISSUE-COMMENTS.md
session_transcript: claude-app:860a6ba4-730e-4113-80e7-290d85a766f1
---

# Summary

Implemented WI-REVIEW-RESPONSE-ISSUE-COMMENTS: wired PR issue comments
into `lrh request review_response`'s fetch, formatting, template
rendering, and early-return gate, so a finding (or clean-pass
confirmation) posted only as a plain issue comment is no longer
silently missed.

# Result

Read the full work item (Required Changes 1-6, Acceptance Criteria,
Non-Goals) before implementing. Changes:

- `src/lrh/integrations/github/pull_reviews.py`: added
  `get_pull_issue_comments(ref)`, fetching via
  `gh api --paginate --slurp repos/{owner}/{repo}/issues/{n}/comments`
  (REST), defensively guarding non-list payloads.
- `src/lrh/integrations/github/formatters.py`: added
  `_collect_issue_comments`, `has_issue_comments`, and
  `format_issue_comments` (mirrors `format_threads_review`'s
  path/URL/author/body shape, using the correct REST field names
  `user.login`/`html_url`, not the GraphQL `author.login`/`url` shape
  used for review threads).
- `src/lrh/assist/request_service.py`: `generate_request()`'s
  `review_response` branch now fetches issue comments alongside review
  threads, extends the "Nothing to resolve" gate to also check
  `has_issue_comments`, and populates a new `ISSUE_COMMENTS` template
  variable. Documented the "always include" heuristic choice (WI
  Required Change 4) with an inline comment — no addressed/unresolved
  state tracking for issue comments, since they have no
  `isResolved`/`isOutdated` equivalent.
- `src/lrh/assist/templates/request/review_response.md`: added
  `{{ISSUE_COMMENTS}}` after `{{UNRESOLVED_THREADS}}`.
- Checked `lrh-review-response`/`lrh-confirm-fixes`/`lrh-land` for
  Required Change 5 (propagation): none call `review_response`'s
  Python API directly, only the CLI, so the fix propagates
  automatically. Found and fixed one stale claim:
  `lrh-land/SKILL.md` Step 4 described `review_response` as
  GraphQL-threads-only; updated (mirrored to `.claude/skills/lrh-land/SKILL.md`)
  to mention the REST issue-comment fetch too.
- Ruled out the review-body-as-findings Non-Goal as already confirmed
  unreachable (per the WI's own Problem/Context section) — no change
  needed there.

Ran diff-mode `/lrh-self-review` (independent cold-context subagent,
since `/lrh-implement` Step 7.5 requires it and this session's own
`Skill` tool cannot invoke it directly due to `disable-model-invocation` —
dispatched as a general-purpose subagent instead, same effect). It found
2 real issues (the stale `lrh-land/SKILL.md` claim above, and the
missing heuristic-choice documentation) and 2 nitpicks (unchanged
"Nothing to resolve" message wording once issue comments are also part
of the gate; minor duplication between the new fetch helper and the
existing `get_pull_comments()`, explicitly permitted by the WI text).
I independently re-verified its top finding (the stale SKILL.md claim)
by reading the file directly before accepting it, per the skill's Step 4.
Both real issues fixed; nitpicks left as-is (Non-Goals scope / explicit
WI permission).

Mid-implementation, `origin/main` advanced under a concurrent session
(PR #547 merged). Rebased cleanly onto the new tip before the final
commit/push; re-ran full validation post-rebase to confirm no drift.

# Validation

- `scripts/format --check` / `scripts/lint`: clean
- `PYTHONPATH="$(pwd)/src" python -m unittest discover -s tests -p '*_test.py'`:
  1093 tests pass (this repo has a known PYTHONPATH gotcha where an
  editable install can resolve to a different checkout's `src/`;
  verified `lrh.integrations.github.formatters.__file__` pointed at
  this worktree before trusting results)
- `lrh validate`: 0 errors (1 pre-existing, unrelated
  `WS-SESSION-ARCHIVE-SYNC` warning)

# Follow-up

- PR #553 open, not yet landed — `/lrh-execute`'s Step 4 (`/lrh-land`
  inline) continues next.
- WI-REVIEW-RESPONSE-ISSUE-COMMENTS stays `proposed` until this PR
  merges and closeout resolves it.
