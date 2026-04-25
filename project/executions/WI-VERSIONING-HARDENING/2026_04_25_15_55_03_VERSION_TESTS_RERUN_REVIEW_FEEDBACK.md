---
execution_id: 2026_04_25_15_55_03_VERSION_TESTS_RERUN_REVIEW_FEEDBACK
prompt_id: PROMPT(WI-VERSIONING-HARDENING:VERSION_TESTS)[2026-04-25T02:05:00-04:00]
work_item: WI-VERSIONING-HARDENING
status: landed
rerun_of: 2026_04_25_07_39_59_VERSION_TESTS
pr:
commit: d30e263
created_at: 2026-04-25T15:55:03+00:00
---

# Summary

Prompt rerun to address review feedback on version integration-test determinism.

# Result

Updated `tests/cli_tests/version_integration_test.py` to handle `PackageNotFoundError` and assert deterministic CLI output in both installed and source-checkout environments.

# Validation

- `python -m unittest tests.cli_tests.version_integration_test tests.version_test`
- `python -m ruff check tests/cli_tests/version_integration_test.py tests/version_test.py`
- `python -m black --check tests/cli_tests/version_integration_test.py tests/version_test.py`

# Follow-up

None.
