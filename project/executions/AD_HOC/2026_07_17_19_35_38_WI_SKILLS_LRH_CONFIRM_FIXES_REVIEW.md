---
execution_id: 2026_07_17_19_35_38_WI_SKILLS_LRH_CONFIRM_FIXES_REVIEW
prompt_id: PROMPT(AD_HOC:WI_SKILLS_LRH_CONFIRM_FIXES_REVIEW)[2026-07-17T19:20:07-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_07_17_18_55_17_WI_SKILLS_LRH_CONFIRM_FIXES
pr: https://github.com/xenotaur/logical_robotics_harness/pull/397
commit: 
created_at: 2026-07-17T19:35:38-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/397
session_transcript: pending
---

# Summary

Address 13 review comments (6 distinct findings) on PR #397
(`/lrh-confirm-fixes` implementation) via `/lrh-review-response`.

# Result

All 6 findings passed presence/validity/feasibility triage and were fixed:

1. **copilot-pull-request-reviewer (x2, superseded by finding 3's fix)** —
   Step 2 wording implied `reviewThreads` supports a server-side
   `isResolved: false` filter; it doesn't. Resolved by finding 3's mechanism
   replacement, not a standalone wording patch.
2. **copilot-pull-request-reviewer (x4)** — the provisional and post-push CI
   commands used the placeholder `<pr>` instead of `<pr-url>`, and both
   omitted `--required` despite the reference doc's own prose recommending
   it (the reference doc's own example command also omitted it). Fixed all
   three locations plus the placeholder inconsistency.
3. **chatgpt-codex-connector + copilot-pull-request-reviewer (x2), P2** —
   the hand-rolled `gh api graphql reviewThreads` query capped at 50 threads
   with no pagination, undermining the "authoritative list" claim on large
   PRs. Verified `src/lrh/integrations/github/pull_reviews.py` already
   contains a fully-paginated `get_pull_review_threads()` (100/page,
   following `pageInfo`). Replaced the hand-rolled query with
   `lrh github threads <pr-url> --mode raw --state unresolved`, a real CLI
   entry point (`src/lrh/cli/github.py`) over that same function —
   live-tested against PR #397 itself.
4. **chatgpt-codex-connector, P2** — the design assumed a thread's *first*
   comment's `databaseId` matches the URL `lrh request review_response`
   surfaces, but `formatters.py:80-81` shows the formatter uses the
   *latest* comment (`nodes[-1]`) — any thread with a reply would have
   silently failed to correlate. Fixed: `lrh github threads` returns every
   comment per thread, so correlation now matches on the same
   latest-comment URL the formatter emits. Verified `request_service.py:125`
   — `lrh request review_response` and `lrh github threads` call the
   *identical* underlying function with the *identical* state filter, so
   this correlation is provably exact, not heuristic.
5. **chatgpt-codex-connector, P2** — the reported merge one-liner didn't
   lock to the checked commit, so a push between the readiness report and
   the human's click could get silently merged unchecked. Added
   `--match-head-commit <sha>` (verified via `gh pr merge --help`).

No comments were skipped. Findings 3 and 4 were the substantive catches —
both are correctness bugs that would have silently produced wrong results
on real PRs (missed threads on large PRs; failed correlation on any
thread with a reply, which is common). Discovering the existing
`get_pull_review_threads()`/`lrh github threads` infrastructure while
investigating also strengthens the original design's Decision 10 (reuse
existing infra) more thoroughly than the original implementation did.

# Validation

```
scripts/version tools  — lrh 0.2.5.dev83, Ruff 0.15.12, Black 25.11.0 confirmed
scripts/format --check --diff  — skipped: no Python files changed (markdown-only skill edits)
scripts/lint  — skipped: no Python files changed
scripts/test  — skipped: no Python files changed
lrh validate  — 0 errors, 0 warnings
diff -r src/lrh/skills/lrh-confirm-fixes/ .claude/skills/lrh-confirm-fixes/  — identical
lrh github threads <pr-url> --mode raw --state unresolved  — live-tested against PR #397, returned correct thread/comment structure
gh pr merge --help / gh pr checks --help  — confirmed --match-head-commit and --required both exist as documented flags
```

# Follow-up

- Update `session_transcript: pending` to `claude-app:<session-id>` after the
  session ends.
- No unresolved comments remain on PR #397 as of this record.
