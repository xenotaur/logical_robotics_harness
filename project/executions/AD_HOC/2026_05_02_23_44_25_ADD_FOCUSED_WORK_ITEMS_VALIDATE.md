---
execution_id: 2026_05_02_23_44_25_ADD_FOCUSED_WORK_ITEMS_VALIDATE
prompt_id: PROMPT(AD_HOC:ADD_FOCUSED_WORK_ITEMS_VALIDATE)[2026-05-02T16:15:00-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: 
commit: 
created_at: 2026-05-02T23:44:25+00:00
---

# Summary

Added a new read-only command, `lrh work-items validate`, with text/JSON output, deterministic diagnostics, and exit codes (`0` clean, `1` validation errors, `2` operational read failure).

# Result

Implemented validation logic in `src/lrh/work_items/validate.py`, integrated the command under `lrh work-items`, reused work-item path discovery for completion via shared discovery helper, added focused unit/CLI tests, and updated top-level README usage guidance.

# Validation

- `python -m unittest tests.work_items_tests.validate_test tests.cli_tests.work_items_test` (pass)
- `scripts/lint` (ruff pass; repository-level black check reported failure outside targeted changed files)
- `python -m black --check src/lrh/cli/main.py src/lrh/work_items/validate.py tests/work_items_tests/validate_test.py tests/cli_tests/work_items_test.py src/lrh/cli/completion_sources.py` (pass)

# Follow-up

- Consider consolidating all work-item discovery and parsing helpers into a shared module for `organize`, completion, and `validate`.
- Investigate repository-level `scripts/lint` black failure outside this prompt scope.
