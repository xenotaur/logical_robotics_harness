---
execution_id: 2026_04_25_06_23_10_WORK_ITEM_PROMPT_DOCS
prompt_id: PROMPT(AD_HOC:WORK_ITEM_PROMPT_DOCS)[2026-04-24T20:15:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-04-25T06:23:10+00:00
---

# Summary

Document and polish the work-item-to-Codex prompt workflow, with emphasis on:

- explicit flow from work item markdown through Codex prompt and PR
- user-facing guidance for when/how to create execution records
- lightweight CLI help-text wording improvements for the structured command

# Result

Completed docs-focused updates in:

- `PROMPTS.md`
- `scripts/prompts/README.md`
- `src/lrh/assist/README.md`
- small `lrh request codex-prompt-from-work-item` help-text polish in `src/lrh/assist/request_cli.py`

No functional behavior changes were introduced.

# Validation

- `scripts/test tests/assist_tests/request_cli_test.py`
- `scripts/test tests/cli_tests/request_test.py`
- `scripts/test tests/scripts_tests/prompt_scripts_test.py`
- `python -m black --check src/lrh/assist/request_cli.py`
- `python -m ruff check src/lrh/assist/request_cli.py`

# Follow-up

- Update `status`, `pr`, and `commit` once PR is opened and revision history is finalized.
