---
execution_id: 2026_05_04_19_00_01_SCRIPTS_DEVELOP_BOOTSTRAP_DIAGNOSTICS
prompt_id: PROMPT(WI-DEV-TOOLCHAIN-RECONCILIATION:SCRIPTS_DEVELOP_BOOTSTRAP_DIAGNOSTICS)[2026-05-04T09:10:00-04:00]
work_item: WI-DEV-TOOLCHAIN-RECONCILIATION
status: landed
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
- Did not add shell-script tests; used manual validation and the repository's canonical validation scripts for this focused script change.

# Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `scripts/develop` (failed in task phase due to restricted package-index access; expected diagnostic printed)
- `scripts/version tools` (re-run after failed `scripts/develop`)

# Follow-up

If contributors repeatedly hit task-phase `scripts/develop` failures in constrained environments, consider adding a short pointer in `scripts/README.md` linking to the same setup-vs-validation guidance now emitted by the script.
