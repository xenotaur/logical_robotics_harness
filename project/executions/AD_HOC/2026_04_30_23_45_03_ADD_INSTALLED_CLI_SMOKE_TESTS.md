---
execution_id: 2026_04_30_23_45_03_ADD_INSTALLED_CLI_SMOKE_TESTS
prompt_id: PROMPT(WI-INSTALLED-PROMPT-WORKFLOW:ADD_INSTALLED_CLI_SMOKE_TESTS)[2026-04-29T22:07:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-04-30T23:45:03+00:00
---

# Summary

Added an installed-package smoke test for LRH prompt workflow commands that runs from an isolated temporary target repository rather than from this checkout root.

Work item `WI-INSTALLED-PROMPT-WORKFLOW` was not present under `project/work_items/`, so this execution was recorded under `AD_HOC` per prompt instructions.

# Result

Implemented `tests/smoke/prompt_cli_install_smoke.py` to:

- create a temporary venv and install LRH from the current checkout
- create a minimal target repo tree with `project/executions/`
- run from that target repo cwd and verify installed CLI commands:
  - `lrh --help`
  - `lrh prompt label --slug example`
  - `lrh prompt record-execution --dry-run ...`

Updated `scripts/README.md` with maintainer instructions for running the prompt CLI install smoke check manually.

# Validation

- `python -m unittest tests.smoke.prompt_cli_install_smoke` (passed with skip in this environment due to unavailable install/build dependencies)
- `scripts/test` (passed)

# Follow-up

- Consider wiring this smoke test into a dedicated script similar to `scripts/smoke_assist_install` if maintainers want a one-command installed prompt workflow smoke path.
