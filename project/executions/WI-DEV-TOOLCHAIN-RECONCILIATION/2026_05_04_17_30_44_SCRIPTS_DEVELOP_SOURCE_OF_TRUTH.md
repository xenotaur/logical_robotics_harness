---
execution_id: 2026_05_04_17_30_44_SCRIPTS_DEVELOP_SOURCE_OF_TRUTH
prompt_id: PROMPT(WI-DEV-TOOLCHAIN-RECONCILIATION:SCRIPTS_DEVELOP_SOURCE_OF_TRUTH)[2026-05-03T11:20:00-04:00]
work_item: WI-DEV-TOOLCHAIN-RECONCILIATION
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-04T17:30:44+00:00
---

# Summary

Consolidated reusable setup documentation to use `scripts/develop` as the source-of-truth entrypoint for LRH's constrained editable development install.

# Result

- Replaced raw constrained editable install commands with `scripts/develop` in:
  - `README.md` canonical setup/release prerequisite guidance.
  - `scripts/README.md` build requirements and dependency notes.
- Kept the raw pip constrained install command in `scripts/develop` only, and added an explicit source-of-truth comment above it.
- Left historical references in prior execution records unchanged to preserve audit history and comply with execution-record immutability guidance.

# Validation

- `scripts/develop` *(failed in this environment while resolving build dependencies from package index: `setuptools>=68` unavailable due to tunnel/proxy restrictions).*
- `scripts/version tools` *(passed).*
- `scripts/format --check --diff` *(passed).*
- `scripts/lint` *(passed).*
- `scripts/test` *(passed; 295 tests, 3 skipped).*

# Follow-up

- If this environment regains package-index access, rerun `scripts/develop` and then repeat the canonical validation sequence end-to-end for parity confirmation.
