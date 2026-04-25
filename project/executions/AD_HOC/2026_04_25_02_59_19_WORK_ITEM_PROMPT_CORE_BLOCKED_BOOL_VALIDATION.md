---
execution_id: 2026_04_25_02_59_19_WORK_ITEM_PROMPT_CORE_BLOCKED_BOOL_VALIDATION
prompt_id: PROMPT(AD_HOC:WORK_ITEM_PROMPT_CORE)[2026-04-24T20:05:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_04_25_02_52_37_WORK_ITEM_PROMPT_CORE_REVIEW_FIXES
pr: draft
commit: f4e6d7cc7bdca1f1fd59f1615e40a45fda3b825f
created_at: 2026-04-25T02:59:19+00:00
---

# Summary

Addressed review feedback around strict `blocked` metadata typing in the work-item prompt parser.

# Result

Replaced permissive boolean coercion for `blocked` with strict bool validation, preventing quoted strings like `"false"` from being interpreted as truthy blocked state. Added direct parser test coverage and CLI-level handled-error coverage for malformed `blocked` values.

# Validation

- python -m unittest tests.assist_tests.work_item_prompt_core_test tests.assist_tests.request_cli_test
- scripts/format
- scripts/lint
- scripts/test

# Follow-up

- If desired, expand strict typing checks for additional frontmatter fields where permissive coercion could hide malformed metadata.
