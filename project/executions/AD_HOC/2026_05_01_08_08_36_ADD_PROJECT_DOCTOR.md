---
execution_id: 2026_05_01_08_08_36_ADD_PROJECT_DOCTOR
prompt_id: PROMPT(WI-INSTALLED-PROMPT-WORKFLOW:ADD_PROJECT_DOCTOR)[2026-04-29T22:10:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-01T08:08:36+00:00
---

# Summary

Added a non-mutating `lrh project doctor` diagnostic command with deterministic text/JSON output and strict exit-code mode for LRH project bootstrap readiness.

`WI-INSTALLED-PROMPT-WORKFLOW` was not present in `project/work_items/`, so `AD_HOC` was used per prompt workflow guidance.

# Result

- Added `lrh project doctor --project-root <path>` in the main CLI under `project` subcommands.
- Implemented readiness diagnostics covering required control-plane files/directories and recommended developer scripts.
- Added explicit error/warning/info findings and recommended `lrh project init --profile prompt-workflow` next step when required scaffolding is missing.
- Added optional `--json` and `--strict` behavior.
- Added CLI tests for empty/minimal/full bootstrap cases and strict/json exit behavior.
- Updated README bootstrap section to document doctor as the first diagnostic command.

# Validation

- `python -m unittest tests/cli_tests/project_doctor_test.py tests/cli_tests/project_init_test.py`
- `scripts/test`

# Follow-up

- Optionally add a profile-target hint (minimal/prompt-workflow/full) based on which files are missing most.
