---
execution_id: 2026_05_03_17_00_36_CI_PARITY_DIAGNOSTICS
prompt_id: PROMPT(WI-DEV-TOOLCHAIN-RECONCILIATION:CI_PARITY_DIAGNOSTICS)[2026-05-03T11:15:00-04:00]
work_item: WI-DEV-TOOLCHAIN-RECONCILIATION
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-03T17:00:36+00:00
---

# Summary

Updated GitHub Actions lint/test workflows to align CI with the documented local/agent dev install path and canonical scripts. Added explicit toolchain diagnostics via `scripts/version tools` and clearer step naming for lint, formatting, and tests.

# Result

- Updated `.github/workflows/lint.yml` to run `scripts/version tools`, `scripts/lint`, and `scripts/format --check --diff` with explicit step names.
- Updated `.github/workflows/tests.yml` to run `scripts/version tools` before `scripts/test`, preserving existing `lrh validate` coverage.
- Kept CI architecture and dependency-install path unchanged (`python -m pip install -e ".[dev]" -c constraints-dev.txt`).

# Validation

- `python -m pip install -e ".[dev]" -c constraints-dev.txt` *(failed in this environment due to package-index/network access restrictions while resolving build dependencies).*
- `scripts/version tools` *(passed; surfaced local tool version mismatches).*
- `scripts/format --check --diff` *(failed due to required Black version mismatch).*
- `scripts/lint` *(failed due to required Ruff version mismatch).*
- `scripts/test` *(passed; 292 tests).*
- Workflow YAML inspected directly; no in-environment GitHub Actions runner execution available.

# Follow-up

- Re-run full validation after provisioning exact contract tool versions (`black==26.3.1`, `ruff==0.15.12`) in the execution environment.
- Confirm GitHub Actions run output after push for end-to-end CI parity evidence.
