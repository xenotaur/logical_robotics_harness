---
execution_id: 2026_04_30_20_49_07_WRAP_EXISTING_PROMPT_SCRIPTS
prompt_id: PROMPT(WI-INSTALLED-PROMPT-WORKFLOW:WRAP_EXISTING_PROMPT_SCRIPTS)[2026-04-29T22:06:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-04-30T20:49:07+00:00
---

# Summary

Converted `scripts/prompts/label-prompt` and `scripts/prompts/record-execution` to thin compatibility wrappers that delegate to LRH package-owned prompt CLI commands.

Work item `WI-INSTALLED-PROMPT-WORKFLOW` was not present under `project/work_items/`, so this execution was recorded under `AD_HOC` per prompt instructions.

# Result

- Legacy prompt scripts now delegate to `lrh prompt ...` when available.
- Local-checkout fallback delegates to `python -m lrh.cli.main prompt ...` with `PYTHONPATH` set to repository `src/`.
- Prompt workflow docs now describe these scripts as compatibility wrappers and identify installed `lrh prompt ...` as the portable interface.
- Script-path tests were updated to validate dry-run behavior still works when invoked from outside repo root.

# Validation

- `pytest -q tests/scripts_tests/prompt_scripts_test.py tests/cli_tests/prompt_test.py`
- `scripts/test`

# Follow-up

- Update `status`, `pr`, and `commit` after PR merge.
