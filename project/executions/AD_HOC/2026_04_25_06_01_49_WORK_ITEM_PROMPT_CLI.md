---
execution_id: 2026_04_25_06_01_49_WORK_ITEM_PROMPT_CLI
prompt_id: PROMPT(AD_HOC:WORK_ITEM_PROMPT_CLI)[2026-04-24T20:10:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-04-25T06:01:49+00:00
---

# Summary

Integrate structured work-item prompt generation into the LRH CLI using:
`lrh request codex-prompt-from-work-item --work-item ... --slug ... --out ...`.

# Result

Implemented CLI wiring in `src/lrh/assist/request_cli.py` with:
- dedicated command parsing for `codex-prompt-from-work-item`
- required `--work-item`, `--slug`, and `--out` arguments
- slug-derived prompt ID generation
- direct prompt file output write path support

Added CLI-level and request-cli unit tests for the new command workflow.

# Validation

- `python -m unittest tests.assist_tests.request_cli_test tests.cli_tests.request_test`
- `black --check src/lrh/assist/request_cli.py tests/assist_tests/request_cli_test.py tests/cli_tests/request_test.py`
- `scripts/lint` (repo baseline formatting issue remains in
  `tests/control_tests/parser_test.py`)

# Follow-up

- If needed, normalize legacy `lrh request codex_prompt_from_work_item` usage docs
  to call out both command forms.
