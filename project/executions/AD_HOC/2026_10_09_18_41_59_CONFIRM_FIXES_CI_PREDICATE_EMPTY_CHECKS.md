---
execution_id: 2026_10_09_18_41_59_CONFIRM_FIXES_CI_PREDICATE_EMPTY_CHECKS
prompt_id: PROMPT(AD_HOC:CONFIRM_FIXES_CI_PREDICATE_EMPTY_CHECKS)[2026-10-09T17:33:12+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/807
commit: 0fbb74a807c3a953f3188ff042f4a8156f4f1152
created_at: 2026-10-09T18:41:59+00:00
agent: claude_app
instruction_source: "ad-hoc: fix false-green in /lrh-confirm-fixes check_ci_predicate when the gh pr checks list is empty right after a push; consider verifying headRefOid"
session_transcript: claude-app:a6e3e7d1-6dca-4a75-999f-73b646ceb1fa
---

# Summary

Ad-hoc fix to `check_ci_predicate` in `/lrh-confirm-fixes`'s
`references/confirm-fixes-workflow.md` § "Bounded background-poll wait". Before
this fix, an empty check list right after a push reported "CI green" (return
0).

# Result

- **Empty, `[]`, or unparseable check list:** the predicate now returns 2
  (pending). This covers real gh's empty-stdout, exit-1 "no checks reported"
  case and the hypothetical `[]` case.
- **Stale PR head:** added an optional expected-head-SHA argument. The
  predicate returns 2 until the PR's `headRefOid` matches. This closes the
  async head-ref window: `gh pr checks` reads `commits(last: 1)` and has no SHA
  field. The poll loop passes `git rev-parse HEAD`.
- **No-CI repos:** the prose now says a repo with no CI times out as "still
  pending" by design.
- **Copies:** the src, `.claude/skills/`, and `.agents/skills/` copies are
  byte-identical. `.gemini/plugins/lrh/` (a generated, already-drifted target)
  is untouched.
- **Tests:** new `tests/packaging_tests/skills_confirm_fixes_ci_predicate_test.py`
  has 12 behavioral cases. It extracts the predicate from each copy and runs it
  against a fake `gh`.
- **Prior art:** no existing work item, proposal, or backlog entry covered this.
- **Self-review:** a diff-mode `/lrh-self-review` ran before the first push.
  Record: `2026_10_09_18_41_00_CONFIRM_FIXES_CI_PREDICATE_EMPTY_CHECKS_SELFREVIEW`.

# Validation

- **Environment:** conda env `LrhCiPredicate`, created with
  `scripts/conda-worktree-env` and bound to this worktree. Python 3.11, Black
  26.3.1, Ruff 0.15.12. pyright is not installed.
- **Checks:** `scripts/format --check --diff`, `scripts/lint`, `scripts/test`,
  and `lrh validate` all passed (0 errors, 0 warnings).
- **New test module:** 12/12 OK.
- **Negative control:** 6/12 fail against `origin/main`'s old predicate.

# Follow-up

- `.gemini/plugins/lrh/skills/` is still behind `src/` in general. Regenerate
  it with `lrh skills install --local --target antigravity` if that copy is
  meant to be kept current.
