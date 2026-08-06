---
execution_id: 2026_08_06_02_50_09_WI_SKILLS_STATUS_CHECK
prompt_id: PROMPT(WI-SKILLS-STATUS-CHECK:WI_SKILLS_STATUS_CHECK)[2026-08-05T21:28:21+00:00]
work_item: WI-SKILLS-STATUS-CHECK
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/495
commit: 88d5d25
created_at: 2026-08-06T02:50:09+00:00
agent: codex_app
instruction_source: project/work_items/proposed/WI-SKILLS-STATUS-CHECK.md
session_transcript: codex-app:current-task
---

# Summary

Implemented `WI-SKILLS-STATUS-CHECK` by adding read-only skill installation
inspection commands for LRH's target-aware skill installer.

# Result

Added `lrh skills status` and `lrh skills check` alongside the existing
`lrh skills install` command. Both commands reuse the same source, target,
scope, and repo-config resolution path as install, but call read-only installer
inspection logic instead of writing skill directories.

The installer now reports per-skill inspection states for missing, up-to-date,
modified, and source-error cases, plus Codex compatibility issues for stripped
Claude-only metadata and invalid `agents/openai.yaml` content. `status` reports
informational output and exits zero; `check` exits nonzero when any inspected
skill is missing, modified, source-error, or compatibility-problematic.

Focused tests cover installer-level inspection, CLI help and exit behavior,
read-only behavior, `all` target resolution, Codex metadata checks, modified
target copies, and symlink safety.

# Validation

- `conda run -n LRH scripts/version tools` — expected Ruff `0.15.12` and Black `26.3.1`; Pylint/Pyright absent as future tooling.
- `conda run -n LRH python -m unittest tests.skills_installer_test tests.cli_tests.skills_test` — 101 tests passed.
- `conda run -n LRH scripts/format --check --diff` — 188 files unchanged.
- `conda run -n LRH scripts/lint` — Ruff passed and Black unchanged.
- `conda run -n LRH scripts/test` — 977 tests passed plus release smokes, when run outside the sandbox because serve tests bind local sockets.
- `conda run -n LRH lrh validate` — 0 errors, 0 warnings.
- `git diff --check` — clean.

# Follow-up

Proceed through `/lrh-land` for PR #495.
