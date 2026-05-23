---
execution_id: 2026_05_22_20_57_32_META_DASHBOARD_VALIDATION_DIAGNOSTICS
prompt_id: PROMPT(AD_HOC:META_DASHBOARD_VALIDATION_DIAGNOSTICS)[2026-05-22T10:05:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-22T20:57:32+00:00
---

# Summary

Add actionable validation diagnostics to `lrh serve` meta dashboard cards so
projects with `Validation status: error` show reproducible next actions and
diagnostic context rather than empty diagnostics.

# Result

Implemented shared meta-card fields for validation diagnostics and next action,
wired them through API/HTML payloads, rendered validation-specific sections for
error cases, and added focused `serve` route tests.

# Validation

- `lrh prompt check-execution --prompt-id "PROMPT(AD_HOC:META_DASHBOARD_VALIDATION_DIAGNOSTICS)[2026-05-22T10:05:00-04:00]" --project-root .`
- `scripts/version tools`
- `scripts/test tests/cli_tests/serve_test.py`
- `scripts/format`
- `scripts/lint`

# Follow-up

- Perform the separate validation/dashboard semantics design pass for lane
  classification, setup/source-state semantics, and deeper validation policy.
