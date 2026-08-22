---
execution_id: 2026_08_22_23_22_45_CONDA_WORKTREE_ENV_SCRIPT_SELFREVIEW
prompt_id: PROMPT(AD_HOC:CONDA_WORKTREE_ENV_SCRIPT_SELFREVIEW)[2026-08-22T23:22:37+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_08_22_04_23_51_CONDA_WORKTREE_ENV_SCRIPT
pr: https://github.com/xenotaur/logical_robotics_harness/pull/600
commit: 58bb3c5c
created_at: 2026-08-22T23:22:45+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/600
session_transcript: claude-app:17bd90a6-1e4a-4b7b-8883-fc13d0d8a192
---

# Summary

PR-mode substitute self-review pass (`/lrh-confirm-fixes` Step 8) on PR
#600's `_CONFIRM` commit (`7dc032d7`). No automated reviewer responded
within a 900s bounded poll, so this substitute pass is the review signal
for this round.

# Result

Dispatched a cold-context `general-purpose` subagent to independently
review the current HEAD diff. Findings: no blocking issues; all 5
previously-fixed threads confirmed genuinely fixed with no residual
variant, no command-injection risk, correct `set -e`/exit-code
propagation for the main paths. 4 non-blocking nits surfaced:

1. `--dry-run --recreate` always previews the create-fresh path, never
   the remove-then-create path, since `ENV_EXISTS` is unconditionally
   forced to 0 under `--dry-run`. **Not fixed** — self-disclosed
   limitation of dry-run's necessarily-approximate preview; the printed
   message already says "assuming does not exist for preview purposes."
2. `|| true` on the stale-`logical-robotics-harness`-uninstall `conda
   run` call swallowed *any* nonzero exit, not just "package not
   installed" -- masking a genuine environment failure instead of
   surfacing it. **Fixed**: now checks `pip show -q` first and only
   skips the uninstall (with an explicit "nothing to remove" message)
   when the package is genuinely absent; any other failure now
   propagates under `set -e` as before.
3. The fake `conda` test double always exited 0 for every subcommand, so
   no test exercised nonzero-exit propagation from `conda create`/`conda
   run`. **Fixed**: added `test_conda_create_failure_aborts_before_develop_runs`,
   asserting a failing `conda create` aborts before any `conda run` call.
4. The reuse test asserted only a `run_lines` count, not which commands
   ran. **Fixed** as a side effect of fix #2's test updates: the fake
   `conda`'s blanket "always installed" exit-0 for `pip show` was itself
   unrealistic and meant the uninstall path was exercised in every test
   even where "not installed" is the common case; the fake conda now
   supports a controllable `pip_show_exit_code` (default 1 = not
   installed), and a new `test_stale_install_present_gets_uninstalled`
   explicitly covers the "installed" path.

Independently re-verified the top finding (item 2) myself by reading the
script directly at the line in question before fixing it, not just
accepting the subagent's claim.

Pushed directly to the open PR branch as commit `58bb3c5c`.

# Validation

- `python -m unittest tests.scripts_tests.conda_worktree_env_test` --
  8/8 pass (was 6/6; 2 new tests added)
- `python -m unittest discover -s tests -p '*_test.py'` -- 1274 tests,
  same pre-existing 21 failures/errors as every prior run this session
  (cross-worktree conda editable-install collision at the shared Python
  environment level -- this git worktree isolates git state, not the
  conda env, so this specific collision remains until the environment
  itself is also isolated per this very script's own purpose)
- `scripts/lint` / `scripts/format --check --diff` -- clean
- `bash -n scripts/conda-worktree-env` -- syntax OK
- `lrh validate` -- 0 errors, 0 warnings

# Follow-up

- CI re-check and REVIEW-LANDED check against this record's own
  post-push `HEAD` still needed before the final merge-readiness verdict.
- Nit 1 (dry-run + --recreate preview incompleteness) remains
  unaddressed by design -- documented above as an accepted, disclosed
  limitation rather than deferred debt.
