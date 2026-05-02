---
execution_id: 2026_05_02_21_35_21_ADD_LRH_WORK_ITEMS_ORGANIZE
prompt_id: PROMPT(AD_HOC:ADD_LRH_WORK_ITEMS_ORGANIZE)[2026-05-02T15:45:00-04:00]
work_item: AD_HOC
status: landed
rerun_of:
pr:
commit:
created_at: 2026-05-02T21:35:21+00:00
---

# Summary

Added `lrh work-items organize` as a conservative organizer that plans/applies missing work-item frontmatter updates and status-bucket moves.

# Result

Implemented a reusable planner/apply module (`src/lrh/work_items/organize.py`), wired a new `lrh work-items organize` CLI subcommand, added focused unit/CLI tests, and documented usage in the top-level README.

# Validation

- `scripts/test` (pass)
- `python -m unittest tests/work_items_tests/organize_test.py tests/cli_tests/work_items_test.py` (pass)
- `python -m lrh.cli.main work-items --help` (pass)
- `python -m lrh.cli.main work-items organize --help` (pass)
- `python -m lrh.cli.main work-items organize --project-root . --dry-run` (pass)
- `scripts/lint` (partial: ruff pass, black check reports pre-existing formatting drift in `tests/control_tests/parser_test.py`)

# Follow-up

- Expand status inference with project-wide evidence/reference checks.
- Add safer link-update support for moved work-item paths.
- Consider broader organizer tests for existing frontmatter edge cases and mixed bucket/file layouts.
