---
execution_id: 2026_10_09_18_41_00_CONFIRM_FIXES_CI_PREDICATE_EMPTY_CHECKS_SELFREVIEW
prompt_id: PROMPT(AD_HOC:CONFIRM_FIXES_CI_PREDICATE_EMPTY_CHECKS_SELFREVIEW)[2026-10-09T18:40:55+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-10-09T18:41:00+00:00
agent: claude-app
instruction_source: "ad-hoc: lrh-self-review diff-mode from lrh-implement Step 7.5 for the confirm-fixes CI-predicate empty-check-list fix"
session_transcript: pending
---

# Summary

Diff-mode `/lrh-self-review` pass run from `/lrh-implement` Step 7.5, before
the PR's first push. It reviewed the uncommitted working-tree diff of the
`check_ci_predicate` empty-check-list fix in
`lrh-confirm-fixes/references/confirm-fixes-workflow.md` (src plus the
`.claude`/`.agents` mirrors) and the new
`tests/packaging_tests/skills_confirm_fixes_ci_predicate_test.py`. A
cold-context `general-purpose` subagent did the review. `rerun_of` is empty by
construction because the primary execution record does not exist yet in
diff-mode.

# Result

The pass was report-only (no `--apply`). It found 4 issues; the session
re-verified them and applied the in-scope fixes before the first push.

1. **Medium:** a stale PR head could still give a false green. Re-verified
   against gh's source: `statusCheckRollup` is `commits(last: 1)`, the PR's
   head as GitHub currently records it, which updates asynchronously after
   `git push`. **Fixed:** the predicate now takes an optional expected head
   SHA and returns 2 until `headRefOid` matches. The poll loop passes
   `git rev-parse HEAD`.
2. **Low:** the tests modeled `[]`, but real gh prints empty stdout and exits
   1 when no checks exist (re-verified in gh's `checks.go`). **Fixed:** the
   fake `gh` now mimics that, and a test covers the real empty-rollup path
   with no required rules.
3. **Low:** the no-CI repo behavior change was undocumented. **Fixed:** the
   prose now says a repo with no CI times out as "still pending" by design.
4. **Nit:** the jq guard has gaps on multi-document or non-array JSON. Real
   `gh --json` cannot produce either. **Not fixed** (out of scope).

# Validation

- Ran the new test module: 12/12 OK.
- Negative control against `origin/main`'s old predicate: 6/12 fail, as
  expected.
- Src and both mirrors are byte-identical (`cmp`).
- `scripts/format --check --diff`, `scripts/lint`, `scripts/test`, and
  `lrh validate` all passed (0 errors, 0 warnings).

# Follow-up

None.
