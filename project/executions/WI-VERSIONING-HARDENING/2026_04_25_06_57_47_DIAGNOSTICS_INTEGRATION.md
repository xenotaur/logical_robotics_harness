---
execution_id: 2026_04_25_06_57_47_DIAGNOSTICS_INTEGRATION
prompt_id: PROMPT(WI-VERSIONING-HARDENING:DIAGNOSTICS_INTEGRATION)[2026-04-25T02:05:00-04:00]
work_item: WI-VERSIONING-HARDENING
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-04-25T06:57:47+00:00
---

# Summary

Integrate LRH package version reporting into diagnostics surfaces with a minimal,
reviewable change set.

# Result

- Updated `scripts/version` to report LRH package metadata via
  `importlib.metadata`.
- Added optional LRH version reporting to `lrh meta where` text and JSON output.
- Added/updated tests for meta diagnostics and the version script.
- Updated `scripts/README.md` documentation for the `scripts/version` behavior.

# Validation

- `python -m unittest tests.meta_tests.where_test tests.scripts_tests.version_test tests.cli_tests.main_test`
- `python -m black --check src/lrh/cli/main.py src/lrh/meta/workspace.py tests/meta_tests/where_test.py tests/scripts_tests/version_test.py`
- `scripts/version`
- `scripts/lint` currently fails due unrelated pre-existing formatting drift in
  `tests/control_tests/parser_test.py`.

# Follow-up

- Optionally update the execution record with final PR/commit references after
  merge metadata is available.
