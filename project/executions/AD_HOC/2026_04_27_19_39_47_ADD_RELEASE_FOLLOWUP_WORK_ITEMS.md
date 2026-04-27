---
execution_id: 2026_04_27_19_39_47_ADD_RELEASE_FOLLOWUP_WORK_ITEMS
prompt_id: PROMPT(AD_HOC:ADD_RELEASE_FOLLOWUP_WORK_ITEMS)[2026-04-27T14:55:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-04-27T19:39:47+00:00
---

# Summary

Add two proposed follow-up work items to split post-versioning release hardening into (1) release-tag CI verification and (2) release-smoke isolation auditing.

# Result

Created `WI-RELEASE-TAG-CI` in `project/work_items/proposed/` with scoped acceptance criteria covering tag-trigger behavior, tag checkout verification/build/release-smoke execution, auditability expectations, and explicit non-scope for publishing.

Created `WI-RELEASE-SMOKE-ISOLATION-AUDIT` in `project/work_items/proposed/` with investigation scope, required diagnostic commands, and decision-oriented acceptance criteria for warning/strict/fail behavior.

No focus/status activation changes were made; both items remain proposed follow-up workstreams.

# Validation

- `scripts/format --check` (fails due to pre-existing formatting issue in `tests/control_tests/parser_test.py`)
- `scripts/lint` (ruff passes; black check fails for the same pre-existing formatting issue)
- `scripts/test` (passes)
- `scripts/validate` (passes; `lrh validate` reports 0 errors and 0 warnings)

# Follow-up

If desired, address pre-existing black formatting drift in `tests/control_tests/parser_test.py` in a separate formatting-only change so repository-wide format/lint checks pass cleanly.
