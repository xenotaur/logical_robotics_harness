---
execution_id: 2026_05_04_02_06_05_DEVELOPER_AGENT_DOCUMENTATION
prompt_id: PROMPT(WI-DEV-TOOLCHAIN-RECONCILIATION:DEVELOPER_AGENT_DOCUMENTATION)[2026-05-03T11:30:00-04:00]
work_item: WI-DEV-TOOLCHAIN-RECONCILIATION
status: in_progress
rerun_of: 
pr: 
commit: 2943e41
created_at: 2026-05-04T02:06:05+00:00
---

# Summary

Added a focused developer/agent workflow section to the top-level README documenting reconciled local, CI, and agent usage for `scripts/version tools`, `scripts/format`, `scripts/lint`, and `scripts/test`, including setup, repair, evidence collection, and environment notes.

# Result

Completed documentation updates in `README.md` with canonical command sequences and agent workflow rules. No new tooling was introduced.

# Validation

- `scripts/version tools` (ran; reported tool-version drift in this execution environment)
- `scripts/format --check --diff` (failed due to required Black `26.3.1` vs installed `25.12.0`)
- `scripts/lint` (failed due to required Ruff `0.15.12` and Black `26.3.1` mismatches in environment)
- `scripts/test` (passed: 292 tests)

# Follow-up

- Re-run `scripts/format --check --diff` and `scripts/lint` in an environment with required Black/Ruff versions to verify full parity.
