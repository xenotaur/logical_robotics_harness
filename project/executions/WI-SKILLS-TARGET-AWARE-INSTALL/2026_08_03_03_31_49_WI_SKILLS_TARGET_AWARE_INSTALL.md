---
execution_id: 2026_08_03_03_31_49_WI_SKILLS_TARGET_AWARE_INSTALL
prompt_id: PROMPT(WI-SKILLS-TARGET-AWARE-INSTALL:WI_SKILLS_TARGET_AWARE_INSTALL)[2026-08-03T03:19:03+00:00]
work_item: WI-SKILLS-TARGET-AWARE-INSTALL
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/473
commit: 
agent: codex_app
instruction_source: project/work_items/proposed/WI-SKILLS-TARGET-AWARE-INSTALL.md
session_transcript: codex-app:current-task
created_at: 2026-08-03T03:31:49+00:00
---

# Summary

Implement `WI-SKILLS-TARGET-AWARE-INSTALL`: make `lrh skills install`
target-aware for Claude and Codex while preserving the existing Claude default.

# Result

- Added `--target claude|codex|all` to `lrh skills install`.
- Preserved the default Claude install target and existing no-target behavior.
- Added Codex user-scope and project-scope install targets:
  `~/.agents/skills/` and `./.agents/skills/`.
- Kept dry-run, force, diff, local-modification detection, and symlink-safety
  behavior on the shared installer path, with Codex-specific safety coverage.
- Updated the skills update guide with Claude/Codex target mappings and the
  interim Codex direct-copy caveat.
- Prior-art check: no existing target-aware skill installer implementation was
  found in `src/`; demand source is the governing proposal and this work item.
- Proactive self-review: a fresh independent Codex sub-agent found missing
  Codex-specific safety coverage; addressed before PR creation with additional
  target-specific tests.

# Validation

- `scripts/version tools` — Black 26.3.1, Ruff 0.15.12, Python 3.11.8;
  Pyright not installed (future tooling).
- `scripts/format --check --diff` — clean.
- `scripts/lint` — Ruff and Black checks passed.
- `conda run -n LRH python -m unittest tests.skills_installer_test tests.cli_tests.skills_test`
  — 51 tests passed.
- `scripts/test` — 873 tests passed. Initial sandboxed run failed on serve
  tests with socket-bind `PermissionError`; reran with approved escalation and
  passed.
- `conda run -n LRH lrh validate` — 0 errors, 0 warnings.
- `git diff --check` — clean.

# Follow-up

- Proceed through `/lrh-land` for PR #473.
