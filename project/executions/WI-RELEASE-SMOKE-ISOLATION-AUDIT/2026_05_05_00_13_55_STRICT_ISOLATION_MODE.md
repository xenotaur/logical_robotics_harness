---
execution_id: 2026_05_05_00_13_55_STRICT_ISOLATION_MODE
prompt_id: PROMPT(WI-RELEASE-SMOKE-ISOLATION-AUDIT:STRICT_ISOLATION_MODE)[2026-05-04T17:20:00-04:00]
work_item: WI-RELEASE-SMOKE-ISOLATION-AUDIT
status: landed
rerun_of: 
pr: 
commit: 
created_at: 2026-05-05T00:13:55+00:00
---

# Summary

Added optional strict pre-install isolation enforcement to `scripts/release-smoke` for release audits.

# Result

Implemented `--strict-isolation` in package-owned release-smoke logic. Default mode still warns and continues when `logical-robotics-harness` or import package `lrh` is visible before installing the wheel. Strict mode fails before the install step with an actionable recommendation to rerun with `--diagnose --preserve`. Documentation now explains the default warning behavior, strict enforcement, and diagnostic preservation workflow.

# Validation

- `scripts/version tools` passed.
- `python -m unittest tests.dev_tests.release_smoke_test` passed.
- `scripts/release-smoke --help` passed and documents `--strict-isolation`.
- `scripts/format --check` passed.
- `scripts/lint` passed.
- `scripts/test` passed.
- `scripts/release-smoke v0.2.3` failed during isolated build dependency installation because package-index access returned tunnel `403 Forbidden`; this is an environment/network limitation before release-smoke isolation behavior is reached.

# Follow-up

Run `scripts/release-smoke v0.2.3 --diagnose` in an environment with package-index access if additional end-to-end release-smoke evidence is needed.
