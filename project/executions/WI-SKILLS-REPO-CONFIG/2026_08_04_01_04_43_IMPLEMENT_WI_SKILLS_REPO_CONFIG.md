---
execution_id: 2026_08_04_01_04_43_IMPLEMENT_WI_SKILLS_REPO_CONFIG
prompt_id: PROMPT(WI-SKILLS-REPO-CONFIG:IMPLEMENT_WI_SKILLS_REPO_CONFIG)[2026-08-04T01:04:31+00:00]
work_item: WI-SKILLS-REPO-CONFIG
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/481
commit:
agent: codex_app
instruction_source: src/lrh/skills/lrh-execute/SKILL.md
session_transcript: codex-app:current-task
created_at: 2026-08-04T01:04:43+00:00
---

# Summary

Implemented `project/agent_skills.yaml` repository-local defaults for LRH skill
installation.

# Result

- Added a PyYAML-backed optional config loader for schema version 1 with
  `sources`, `targets`, `scope`, and non-destructive `install.overwrite`
  handling.
- Added a resolved install plan so `lrh skills install` applies CLI flags over
  repo config over conventional defaults.
- Preserved default behavior when no repo config exists: `lrh-package` source,
  Claude target, user scope.
- Added `--scope user|project`; retained `--local` as a project-scope shortcut.
- Ensured repo config cannot enable destructive overwrite; overwrite remains
  gated by explicit `--force`.
- Documented the config schema in `docs/reference/schemas/agent-skills-config.md`
  and linked it from the skill install how-to.
- Fresh independent Codex self-review found one P2 issue: configured
  `scope: project` could not be overridden back to user scope. This was fixed
  with the new `--scope` CLI flag and regression coverage.

# Validation

- `conda run -n LRH python -m unittest tests.skills_installer_test tests.cli_tests.skills_test` — 78 tests passed.
- `conda run -n LRH scripts/version tools` — Black/Ruff versions matched; Pylint/Pyright not installed as expected future tooling.
- `conda run -n LRH scripts/format --check --diff` — passed.
- `conda run -n LRH scripts/lint` — passed.
- `conda run -n LRH scripts/test` — 918 tests passed, including smoke checks.
- `conda run -n LRH lrh validate` — 0 errors, 0 warnings.
- `git diff --check origin/main...HEAD` — passed after the scope-review fix.

# Follow-up

- Open and land the PR through `/lrh-land`.
