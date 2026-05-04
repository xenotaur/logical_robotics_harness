---
execution_id: 2026_05_04_01_39_45_AGENT_PROMPT_HARDENING
prompt_id: PROMPT(WI-DEV-TOOLCHAIN-RECONCILIATION:AGENT_PROMPT_HARDENING)[2026-05-03T11:25:00-04:00]
work_item: WI-DEV-TOOLCHAIN-RECONCILIATION
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-05-04T01:39:45+00:00
---

# Summary

Updated `src/lrh/assist/templates/request/review_response.md` to harden review-response repair instructions around canonical script usage, explicit formatter/linter repair loops, and required evidence for drift or non-reproduction claims.

# Result

- Added canonical validation command set (`scripts/version tools`, `scripts/lint`, `scripts/format --check --diff`, `scripts/test`).
- Added explicit prohibition on substituting direct `black`/`ruff` commands for canonical scripts.
- Added Black-specific and Ruff-specific repair-and-revalidate command sequences.
- Added explicit requirement not to manually rewrap Black formatting.
- Added required evidence bundle before claiming pre-existing drift, unrelated drift, or cannot reproduce.

# Validation

- `scripts/version tools` (ran)
- `scripts/format --check --diff` (blocked by local Black version mismatch: required 26.3.1, installed 25.12.0)
- `scripts/lint` (blocked by local Ruff/Black version mismatch: required Ruff 0.15.12 and Black 26.3.1)
- `scripts/test` (passed)

# Follow-up

No intentional behavior deferrals in template scope. Environment-local tool version mismatches prevented full canonical lint/format validation in this run.
