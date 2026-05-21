---
execution_id: 2026_05_21_16_40_26_SERVE_CONSUME_RESOLVED_META_STATE
prompt_id: PROMPT(AD_HOC:SERVE_CONSUME_RESOLVED_META_STATE)[2026-05-19T14:15:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-21T16:40:26+00:00
---

# Summary

Update `lrh serve` meta project-card source-state handling to consume shared
resolved local meta state, including actionable diagnostics for remote-only
registrations.

# Result

Implemented resolver-backed source-state mapping in serve project cards,
added diagnostics and guidance for missing/local-binding states, and expanded
serve route tests for live/missing-project/missing-repo/needs-local-checkout
coverage.

# Validation

- `scripts/version tools`
- `scripts/test tests/cli_tests/serve_test.py`
- `scripts/lint`
- `scripts/format --check`
- `lrh validate`

# Follow-up

- Keep focus/workstream/work-item/detail counts as explicit capability gaps
  until shared APIs expose those fields.
