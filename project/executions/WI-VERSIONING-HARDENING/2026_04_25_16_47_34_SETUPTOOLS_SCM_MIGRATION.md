---
execution_id: 2026_04_25_16_47_34_SETUPTOOLS_SCM_MIGRATION
prompt_id: PROMPT(WI-VERSIONING-HARDENING:SETUPTOOLS_SCM_MIGRATION)[2026-04-25T02:30:00-04:00]
work_item: WI-VERSIONING-HARDENING
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-04-25T16:47:34+00:00
---

# Summary

Migrated package version configuration from static `project.version` to `setuptools-scm` dynamic versioning and kept CLI version reporting sourced from installed package metadata.

# Result

Updated `pyproject.toml` build metadata for `setuptools-scm`, adjusted CLI tests to avoid asserting a static `pyproject` version value, added an install-mode smoke test covering editable and wheel installs, and documented metadata-backed version reporting in the repository README.

# Validation

- `python -m ruff check tests/cli_tests/main_test.py tests/scripts_tests/version_install_smoke_test.py src/lrh/version.py`
- `python -m black --check tests/cli_tests/main_test.py tests/scripts_tests/version_install_smoke_test.py src/lrh/version.py`
- `python -m unittest tests.version_test tests.cli_tests.main_test tests.cli_tests.version_integration_test tests.scripts_tests.version_install_smoke_test`

# Follow-up

Populate `pr` and `commit` metadata after PR creation and merge flow is complete.
