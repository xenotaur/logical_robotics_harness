---
execution_id: 2026_04_26_20_04_32_SMOKE_TEST_LAYOUT_AND_SCRIPT
prompt_id: PROMPT(AD_HOC:SMOKE_TEST_LAYOUT_AND_SCRIPT)[2026-04-26T10:00:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: pending
commit: 212aa135070c0e324b443e8866bfb196ac7a6a2f
created_at: 2026-04-26T20:04:32+00:00
---

# Summary

Separated heavyweight packaging/install verification from the fast unit suite by moving the install smoke test into `tests/smoke/`, adding a dedicated `scripts/smoke` entry point, and documenting the split in `scripts/README.md`.

# Result

- Moved `tests/scripts_tests/version_install_smoke_test.py` to `tests/smoke/version_install_smoke.py` so it is excluded from `scripts/test` discovery.
- Added `scripts/smoke` to discover only `tests/smoke/*_smoke.py`.
- Updated testing docs to describe fast vs smoke test conventions.
- Preserved existing subprocess timeout behavior in the smoke test.

# Validation

- `scripts/test` (pass)
- `scripts/smoke` (pass; smoke test skipped in this environment due to unavailable build dependencies)
- `scripts/lint` (fails: black check reports pre-existing formatting issue in `tests/control_tests/parser_test.py`)
- `scripts/format --check` (fails: pre-existing formatting issue in `tests/control_tests/parser_test.py`)

# Follow-up

- Populate the `pr` field after the PR reference is finalized.
