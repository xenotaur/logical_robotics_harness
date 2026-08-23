---
execution_id: 2026_08_22_04_23_51_CONDA_WORKTREE_ENV_SCRIPT
prompt_id: PROMPT(AD_HOC:CONDA_WORKTREE_ENV_SCRIPT)[2026-08-22T04:23:07+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/600
commit: cabbb9ab21b63ea9b8b1a265f6f81bab9b266ae2
created_at: 2026-08-22T04:23:51+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/600
session_transcript: claude-app:17bd90a6-1e4a-4b7b-8883-fc13d0d8a192
---

# Summary

Added `scripts/conda-worktree-env`, a per-worktree conda environment
bootstrap script, diagnosed and requested while landing PR #557: multiple
worktrees of this repo sharing one conda environment silently steal the
editable `lrh` install from each other via `scripts/develop`.

# Result

Created `scripts/conda-worktree-env` (executable bash script) with
`--python`, `--recreate`, `--dry-run`, and `-h/--help` flags. It creates
or reuses a named conda environment, then runs `scripts/develop` inside it
via `conda run -n <name> --cwd <repo-root> --no-capture-output`. Sources
packages from `pyproject.toml`'s `[dev]` extra constrained by
`constraints-dev.txt` (same as CI), deliberately not from
`environment.yml`, which was found to be a stale `conda env export`
snapshot carrying two different dev-version pins of the same package
under its current and a prior project name (`lrh` vs.
`logical-robotics-harness`). Documented in `scripts/README.md` alongside
the existing `develop`/`update` entries. Opened
[PR #600](https://github.com/xenotaur/logical_robotics_harness/pull/600).

# Validation

- `bash -n scripts/conda-worktree-env` — syntax OK
- `scripts/conda-worktree-env --help` — renders correctly
- `scripts/conda-worktree-env <new-name> --dry-run` — correct create path
- `scripts/conda-worktree-env <existing-name> --dry-run` (against the
  pre-existing `LRH` env) — correct reuse path, no accidental mutation
- `scripts/check-workflows` — all workflow YAML valid (untouched by this
  change; ran as part of the standard local validation sequence)
- `lrh validate` — 0 errors, 0 warnings

# Follow-up

- Not yet exercised for real (only `--dry-run`) — the actual `conda
  create` + `scripts/develop` path should be run for real once, in a
  throwaway env, before this is trusted as the default agent-onboarding
  step.
- `environment.yml`'s stale dual-pin (`lrh` vs
  `logical-robotics-harness`) is noted here as context but not fixed by
  this PR — flagged as a separate small cleanup opportunity.
