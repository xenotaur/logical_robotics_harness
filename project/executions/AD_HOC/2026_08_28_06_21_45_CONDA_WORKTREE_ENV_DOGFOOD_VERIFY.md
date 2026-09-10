---
execution_id: 2026_08_28_06_21_45_CONDA_WORKTREE_ENV_DOGFOOD_VERIFY
prompt_id: PROMPT(AD_HOC:CONDA_WORKTREE_ENV_DOGFOOD_VERIFY)[2026-08-28T06:21:37+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_08_22_04_23_51_CONDA_WORKTREE_ENV_SCRIPT
pr: https://github.com/xenotaur/logical_robotics_harness/pull/600
commit: cabbb9ab21b63ea9b8b1a265f6f81bab9b266ae2
created_at: 2026-08-28T06:21:45+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/600
session_transcript: claude-app:17bd90a6-1e4a-4b7b-8883-fc13d0d8a192
---

# Summary

Post-merge dogfood verification of `scripts/conda-worktree-env` (PR #600),
closing the gap `/lrh-work-remains` flagged: the script had only ever been
exercised via `--dry-run` and the hermetic fake-`conda` test suite, never
run for real end-to-end.

# Result

Ran `scripts/conda-worktree-env LrhWorktreeSmokeTest` for real (no
`--dry-run`) against the merged worktree, both the create and reuse
paths:

- **Create path:** built a fresh conda env (`python=3.11.16`), installed
  from `pyproject.toml`'s `[dev]` extra constrained by
  `constraints-dev.txt`. `pip show lrh` confirmed `Editable project
  location` pointed at the exact worktree the script was run from.
  Tool versions came out exactly matching this repo's pins
  (`ruff 0.15.12`, `black 26.3.1`) with zero manual intervention -- the
  opposite of the shared `base` env's behavior throughout this session,
  which needed manual re-upgrades twice.
- **Functional checks inside the new env:** `lrh validate` -- 0 errors,
  0 warnings; `scripts/lint` -- all checks passed.
- **Reuse path:** ran the script a second time against the same env
  name -- correctly reported "Reusing existing environment," did not
  recreate it, re-ran `scripts/develop`, and the editable install was
  cleanly reinstalled (pip uninstalled/reinstalled the same version, no
  drift).
- Removed the throwaway `LrhWorktreeSmokeTest` env afterward
  (`conda env remove -n LrhWorktreeSmokeTest -y`) -- confirmed gone via
  `conda env list`.

Both the create and reuse code paths work exactly as designed, confirmed
against real conda/pip behavior, not just the hermetic fake-`conda` test
double.

# Validation

- `pip show lrh` (inside the new env) -- Editable project location
  matched the worktree
- `scripts/version tools` (inside the new env) -- ruff/black versions
  matched `constraints-dev.txt`
- `lrh validate` (inside the new env) -- 0 errors, 0 warnings
- `scripts/lint` (inside the new env) -- all checks passed
- `conda env list` -- confirmed `LrhWorktreeSmokeTest` removed after cleanup

# Follow-up

- None. This closes the dogfooding gap `/lrh-work-remains` identified;
  no further verification of this script is planned.
