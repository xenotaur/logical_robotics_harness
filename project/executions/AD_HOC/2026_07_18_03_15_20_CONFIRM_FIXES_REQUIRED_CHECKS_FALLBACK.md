---
execution_id: 2026_07_18_03_15_20_CONFIRM_FIXES_REQUIRED_CHECKS_FALLBACK
prompt_id: PROMPT(AD_HOC:CONFIRM_FIXES_REQUIRED_CHECKS_FALLBACK)[2026-07-18T03:12:31-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/400
commit: a405f02bf79cecf159def4d1689294c0ece09bbf
created_at: 2026-07-18T03:15:20-04:00
agent: claude_app
instruction_source: ad-hoc task description (gh pr checks --required false-negative fix for /lrh-confirm-fixes, discovered verifying PR #399)
session_transcript: claude-app:e8331ce5-44b4-4ce4-bb6c-fa623700836f
---

# Summary

Fixed a usability bug in `/lrh-confirm-fixes`'s CI check mechanism,
discovered during the skill's first real-world invocation (verifying PR
#399 on this repo). `gh pr checks <pr-url> --required --json name,state,bucket`
exited 1 with "no required checks reported on the '<branch>' branch" even
though CI was genuinely running and passing — the repo has no
required-check branch-protection rule, so `--required` has nothing to
filter to and the command errors instead of returning an empty or
unfiltered list.

# Result

Added a documented fallback at both CI reads in
`src/lrh/skills/lrh-confirm-fixes/SKILL.md` (Step 2 provisional check, Step
8 post-push re-check) and in `references/confirm-fixes-workflow.md`'s "CI
check mechanism" section: on a "no required checks reported" exit, retry
with `gh pr checks <pr-url> --json name,state,bucket` (no `--required`) and
aggregate over all reported checks, using the same green/failing/pending
rules. Mirrored to `.claude/skills/lrh-confirm-fixes/`.

# Validation

```
scripts/version tools  — lrh CLI present, Ruff 0.15.12, Black 26.3.1 (LRH conda env)
scripts/format --check --diff  — 179 files unchanged
scripts/lint  — All checks passed (ruff + black)
lrh validate  — 0 errors, 0 warnings
diff -r src/lrh/skills/lrh-confirm-fixes/ .claude/skills/lrh-confirm-fixes/  — no differences
Reproduction: `gh pr checks https://github.com/xenotaur/logical_robotics_harness/pull/389 --required --json name,state,bucket`
  → exit 1, "no required checks reported on the 'bolt-fast-walk-pruning-5925340555257425629' branch"
Fallback verification: `gh pr checks https://github.com/xenotaur/logical_robotics_harness/pull/389 --json name,state,bucket`
  → exit 0, 5 checks (coverage, installed-wheel-smoke, lint, Check workflow files, tests), all bucket: pass
```

No Python was touched (skill docs only), so `scripts/test` was not run.

# Follow-up

- Update `session_transcript: pending` to the real session id after the
  session ends.
- After PR #400 merges, set `status: landed` and fill in `commit`.
