---
execution_id: 2026_04_27_04_18_19_SMOKE_CI_INTEGRATION
prompt_id: PROMPT(AD_HOC:SMOKE_CI_INTEGRATION)[2026-04-26T10:10:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: pending
commit: pending
created_at: 2026-04-27T04:18:19+00:00
---

# Summary

Integrated smoke tests into CI as a dedicated workflow so fast PR feedback remains focused on unit/lint/format checks while heavyweight packaging/install smoke validation is still available on explicit triggers.

# Result

- Added `.github/workflows/smoke.yml` with a separate smoke job that runs `scripts/smoke`.
- Configured smoke triggers for manual dispatch, weekly schedule, and release-tag pushes (`v*`) to avoid slowing ordinary PR validation.
- Added timeout controls at job and smoke step levels.
- Updated `README.md` testing-tier documentation with explicit CI expectations for fast vs smoke validation paths.

# Validation

- `scripts/test` (pass)
- `scripts/smoke` (pass; smoke test skipped in this environment due to missing build/install prerequisites)
- `scripts/lint` (fails: black check reports pre-existing formatting issue in `tests/control_tests/parser_test.py`)
- `scripts/format --check` (fails: pre-existing formatting issue in `tests/control_tests/parser_test.py`)

# Follow-up

- Populate the `pr` field after the PR reference is finalized.
