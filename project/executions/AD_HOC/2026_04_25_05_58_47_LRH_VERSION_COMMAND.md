---
execution_id: 2026_04_25_05_58_47_LRH_VERSION_COMMAND
prompt_id: PROMPT(AD_HOC:LRH_VERSION_COMMAND)[2026-04-25T01:54:09-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-04-25T05:58:47+00:00
---

# Summary

Added package-backed LRH version reporting via CLI with both `lrh --version` and
`lrh version`, plus focused CLI tests and README command documentation.

# Result

Implemented a new `src/lrh/version.py` helper that reads installed distribution
metadata using `importlib.metadata.version("logical-robotics-harness")` with a
deterministic `lrh unknown` fallback when metadata is unavailable. Wired the
main CLI to expose version output consistently for both command forms and kept
existing `scripts/version` behavior unchanged as a developer diagnostics script.

# Validation

- python -m unittest tests/cli_tests/main_test.py
- scripts/lint (fails format check due pre-existing unrelated file)
- scripts/format --check (fails due pre-existing unrelated file)
- scripts/test

# Follow-up

- Optional future cleanup: format `tests/control_tests/parser_test.py` in a
  separate dedicated formatting change.
