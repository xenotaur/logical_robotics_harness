---
execution_id: 2026_05_01_21_40_03_ADD_PROMPT_CHECK_EXECUTION
prompt_id: PROMPT(WI-INSTALLED-PROMPT-WORKFLOW:ADD_PROMPT_CHECK_EXECUTION)[2026-05-01T17:40:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-01T21:40:03+00:00
---

# Summary

Added installed CLI support for `lrh prompt check-execution` to search execution records by `prompt_id`, report status/path matches deterministically, and return soft-idempotence-oriented exit codes.

Work item `WI-INSTALLED-PROMPT-WORKFLOW` was not present under `project/executions/`, so this run is recorded as `AD_HOC` per prompt instructions.

# Result

Implemented `check-execution` in `src/lrh/prompt_workflow.py`, added unit/CLI coverage, and updated prompt-workflow documentation.

# Validation

- `python -m unittest tests.assist_tests.prompt_workflow_test tests.cli_tests.prompt_test`
- `scripts/test`

# Follow-up

- Fill in `pr` and `commit` fields after PR merge metadata is available.
