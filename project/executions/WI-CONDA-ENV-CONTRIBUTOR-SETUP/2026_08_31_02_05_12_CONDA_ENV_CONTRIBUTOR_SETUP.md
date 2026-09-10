---
execution_id: 2026_08_31_02_05_12_CONDA_ENV_CONTRIBUTOR_SETUP
prompt_id: PROMPT(WI-CONDA-ENV-CONTRIBUTOR-SETUP:CONDA_ENV_CONTRIBUTOR_SETUP)[2026-08-30T09:02:42+00:00]
work_item: WI-CONDA-ENV-CONTRIBUTOR-SETUP
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/656
commit: bbc5ff46073fe28f325fa1e643c21c0a0ce8183f
created_at: 2026-08-31T02:05:12+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-CONDA-ENV-CONTRIBUTOR-SETUP.md
session_transcript: claude-app:33549920-d2fb-4cdd-9c91-510fa180d3e4
---

# Summary

Implemented `WI-CONDA-ENV-CONTRIBUTOR-SETUP`: retired the stale
`environment.yml`/`scripts/update` pair and documented a new-contributor
conda bootstrap path, via `/lrh-execute`.

# Result

- Ran `/lrh-design` earlier in this session to work through the WI's
  open questions (regenerate vs. retire `environment.yml`; doc
  placement; conda vs. venv), including reconciliation with
  `PROP-DEV-TOOLCHAIN-ENV-RESOLUTION`'s adopted Option C.
- Deleted `environment.yml` and `scripts/update`.
- Added `docs/how-to/project-setup/conda-environment.md` (new-contributor
  conda bootstrap guide, distinct from `scripts/conda-worktree-env`'s
  per-worktree agent-isolation use case; notes venv as an equally valid
  alternative; explains why `environment.yml` is gone).
- Updated `README.md`'s Environment notes section and
  `scripts/README.md`'s `conda-worktree-env` description to point at the
  new doc.
- Updated `scripts/conda-worktree-env`'s help text/comments (not its
  logic) to stop referencing the deleted file.
- Added `docs/how-to/project-setup/README.md`'s index entry for the new
  page.
- Recorded the design decision, including explicit Option C
  reconciliation, directly in the WI's own body (`## Design Decision`
  section) — added after a pre-push `/lrh-self-review` diff-mode pass
  found the acceptance criteria required this to be a durable, recorded
  artifact rather than only conversational reasoning.
- Opened [PR #656](https://github.com/xenotaur/logical_robotics_harness/pull/656).

# Validation

- `scripts/version tools`
- `scripts/format --check --diff` — clean
- `scripts/lint` — clean
- `scripts/test` — 1529 tests, OK
- `lrh validate` — 0 errors, 1 pre-existing unrelated warning
  (`FRONTMATTER_LINT_UNSAFE_SCALAR` on
  `WI-GATE-STALENESS-INSTALLED-TARGET-FINGERPRINT.md`, untouched by this
  branch)
- `/lrh-self-review` diff-mode pass before first push — see
  `project/executions/AD_HOC/2026_08_31_02_03_54_CONDA_ENV_CONTRIBUTOR_SETUP_SELFREVIEW.md`

# Follow-up

None identified beyond normal review/merge/closeout.
