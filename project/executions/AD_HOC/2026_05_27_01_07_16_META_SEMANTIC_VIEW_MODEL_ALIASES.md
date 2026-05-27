---
execution_id: 2026_05_27_01_07_16_META_SEMANTIC_VIEW_MODEL_ALIASES
prompt_id: PROMPT(AD_HOC:META_SEMANTIC_VIEW_MODEL_ALIASES)[2026-05-26T20:00:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 7ad88d0
created_at: 2026-05-27T01:07:16+00:00
---

# Summary

Add semantic meta operational-triage view-model field names as canonical
projections while retaining legacy aliases for compatibility.

# Result

- Added semantic alias properties on `ProjectOperationalCard` for
  `project_source_access`, `control_plane_validation`, `triage_lane`,
  `lrh_capability_gaps`, and `other_diagnostics`.
- Updated `/api/meta` project card payloads to include semantic fields while
  preserving legacy aliases (`source_state`, `validation_status`, `lane`,
  `capability_gaps`, `diagnostics`).
- Added transitional fields `project_issues` and `operator_warnings` as empty
  lists for future expansion without behavior changes.
- Added focused tests validating semantic/legacy parity in dashboard model and
  API payload projections.

# Validation

- `scripts/version tools`
- `python -m unittest tests.ux_tests.dashboard_test tests.cli_tests.serve_test`
- `scripts/lint`
- `scripts/format`
- `scripts/lint`
- `scripts/test`

# Follow-up

- Consider migrating additional internal render/read call sites to semantic
  field names first, while preserving legacy aliases during transition.
- Expand `project_issues` and `operator_warnings` from derived signals in a
  dedicated follow-up when semantics are finalized.
