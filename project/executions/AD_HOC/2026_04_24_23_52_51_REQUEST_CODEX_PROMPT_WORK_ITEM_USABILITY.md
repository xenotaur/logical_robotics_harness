---
execution_id: 2026_04_24_23_52_51_REQUEST_CODEX_PROMPT_WORK_ITEM_USABILITY
prompt_id: PROMPT(AD_HOC:REQUEST_CODEX_PROMPT_WORK_ITEM_USABILITY)[2026-04-24T19:46:18-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: pending
commit: 562cb90
created_at: 2026-04-24T23:52:51+00:00
---

# Summary

Improved usability for `lrh request codex_prompt_from_work_item` by adding
deterministic positional work-item resolution, explicit-flag precedence, and
default style-guide resolution to `STYLE.md`.

# Result

- Implemented scoped work-item lookup across
  `project/work_items/{proposed,active,resolved,abandoned}`.
- Preserved explicit fallback support via `--work-item-file` and
  `--style-file`.
- Added/updated tests for resolution behavior, ambiguity handling, and style
  defaults/overrides.
- Updated assist documentation and CLI help text for shorthand usage.

# Validation

- `python -m unittest tests.assist_tests.request_service_test`
- `python -m unittest tests.cli_tests.request_test`
- `python -m unittest tests.assist_tests.request_service_test tests.cli_tests.request_test`
- `scripts/lint`
- `scripts/format --check` (fails due to pre-existing unrelated formatting drift
  in `tests/control_tests/parser_test.py`)
- `python -m black --check src/lrh/assist/request_service.py src/lrh/assist/request_cli.py tests/assist_tests/request_service_test.py`
- `scripts/test`

# Follow-up

- Populate `pr` with the PR identifier once opened.
