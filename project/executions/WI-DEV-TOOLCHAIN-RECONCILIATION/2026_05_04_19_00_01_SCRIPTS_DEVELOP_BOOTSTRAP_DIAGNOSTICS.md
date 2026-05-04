---
execution_id: 2026_05_04_19_00_01_SCRIPTS_DEVELOP_BOOTSTRAP_DIAGNOSTICS
prompt_id: PROMPT(WI-DEV-TOOLCHAIN-RECONCILIATION:SCRIPTS_DEVELOP_BOOTSTRAP_DIAGNOSTICS)[2026-05-04T09:10:00-04:00]
work_item: WI-DEV-TOOLCHAIN-RECONCILIATION
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-05-04T19:00:01+00:00
---

# Summary

Updated `scripts/develop` failure handling so editable install failures print a concise, task-phase-aware diagnostic to stderr while preserving nonzero exit behavior and the canonical install command.

# Result

- Added explicit exit-code capture for the canonical constrained editable install command.
- Added a targeted diagnostic block that distinguishes setup/bootstrap failures from task-phase validation when package-index access is restricted.
- Kept success-path behavior unchanged; the script still exits nonzero on install failure.
- Added focused regression tests under `tests/scripts_tests/develop_test.py` to validate failure-path diagnostics and exit-code preservation.

# Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`

# Follow-up

If contributors repeatedly hit task-phase `scripts/develop` failures in constrained environments, consider adding a short pointer in `scripts/README.md` linking to the same setup-vs-validation guidance now emitted by the script.
