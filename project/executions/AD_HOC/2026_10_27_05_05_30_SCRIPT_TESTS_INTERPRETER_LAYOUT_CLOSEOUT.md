---
execution_id: 2026_10_27_05_05_30_SCRIPT_TESTS_INTERPRETER_LAYOUT_CLOSEOUT
prompt_id: PROMPT(AD_HOC:SCRIPT_TESTS_INTERPRETER_LAYOUT_CLOSEOUT)[2026-10-27T05:05:30+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/843
commit: a53d324e278daeb3359648de6c4ee6dc28fbe7bb
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/843
session_transcript: claude-app:0e4e3c2a-6f50-4437-97b6-1a9381812245
created_at: 2026-10-27T05:05:30+00:00
---

# Summary

Backfill primary record for PR #843 (harden desktop script tests against
interpreter layout; warn on wrong env). The PR was opened ad hoc in a
debugging session, outside `/lrh-implement`, so no primary implementation
record existed; this record is created by `/lrh-land` Step 7 (backfill path)
and carries the run's CHAIN-NOTE.

# Result

PR #843 merged (merge commit a53d324e) via `/lrh-land`.

- Original change: `tests/scripts_tests/desktop_modes_test.py` `_tools_dir()`
  links missing `python`/`black`/`ruff`/`pip` into the sanitized test PATH, so
  the desktop script tests no longer depend on the interpreter's directory
  layout (Homebrew's `python3` ships only `python3`); `scripts/test`
  `warn_if_wrong_environment` warns on stderr when `CONDA_PREFIX`/`VIRTUAL_ENV`
  is set but `$PYTHON` resolves outside it.
- One review-response round (`_REVIEW` record): two Copilot test-coverage
  threads, both fixed with new tests and resolved (`_CONFIRM` record).
- One substitute PR-mode self-review (`_SELFREVIEW` record): clean, 0 findings.
- Root cause of the originating failure was local (Homebrew `python3` ahead of
  the active conda env on PATH after nested-shell `.bashrc` re-runs; fixed in
  the user's dotfiles, not in this repo).

CHAIN-NOTE: cycles=1; stops=0; gates=[merge]; friction=ci-slow; self_review_rounds=1; note="backfill path (PR opened ad hoc); single P3 review-response round on 2 Copilot test-coverage threads, both Clear-satisfied; first CI poll timed out at 900s on a slow desktop (ubuntu) job, second poll green"

# Validation

- Full suite on the PR branch before merge: 2319 tests OK.
- `scripts/format --check`, `scripts/lint`, `lrh validate`: clean.
- CI on the merged head `bc147d7e`: 7 of 7 checks passing.

# Follow-up

- Unifying the bare `python` calls in `scripts/version`, `scripts/lint` and
  `scripts/clean` with `${PYTHON:-python3}` remains deferred (the desktop
  tests set `PYTHON` to a fake interpreter in every run, so it needs its own
  change).
- Speeding up the test suite (about 190s) was discussed but not started.
