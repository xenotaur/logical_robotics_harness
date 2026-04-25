---
execution_id: 2026_04_25_02_52_37_WORK_ITEM_PROMPT_CORE_REVIEW_FIXES
prompt_id: PROMPT(AD_HOC:WORK_ITEM_PROMPT_CORE)[2026-04-24T20:05:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_04_25_02_32_43_WORK_ITEM_PROMPT_CORE
pr: draft
commit: 8729d37817d9d78301cc06591c6cb52aec2a434d
created_at: 2026-04-25T02:52:37+00:00
---

# Summary

Addressed review feedback for the work-item prompt core by fixing wrapped bullet parsing and mapping malformed work-item frontmatter failures to handled CLI errors.

# Result

Implemented continuation-line preserving bullet parsing in `work_item_prompt_core` so multi-line bullet caveats are retained in generated prompt sections. Updated request CLI error handling to catch `ValueError` and return standard user-facing error behavior (exit code 2, stderr message) instead of uncaught tracebacks.

# Validation

- python -m unittest tests.assist_tests.work_item_prompt_core_test tests.assist_tests.request_cli_test
- scripts/format
- scripts/lint
- scripts/test

# Follow-up

- Consider a future parser enhancement for preserving nested bullet structure (not just flattened wrapped text) if needed by prompt fidelity requirements.
