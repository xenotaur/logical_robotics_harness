---
execution_id: 2026_05_20_12_33_16_META_INSPECT_LIST_SETUP_STATE
prompt_id: PROMPT(AD_HOC:META_INSPECT_LIST_SETUP_STATE)[2026-05-19T14:10:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-20T12:33:16+00:00
---

# Summary

Update `lrh meta inspect` and `lrh meta list` output so setup/debug state is grouped and actionable for meta/serve local-state workflows.

# Result

- `meta inspect` now renders grouped sections for workspace, identity, checkout, project, storage, and setup state.
- Inspect uses shared local-state resolver context and displays observation checks as `status as of <timestamp>`.
- `meta list` now includes compact setup triage fields (`setup_checked_as_of`, `checkout_storage`).
- Runtime and CLI inspect tests were updated to validate the new output shape.

# Validation

- `python -m pytest tests/meta_tests/inspect_test.py tests/meta_tests/list_test.py -q`
- `scripts/version tools`
- `scripts/test` (fails in existing `tests/cli_tests/serve_test.py` route assertions with HTTP 404)
- `scripts/lint`
- `scripts/format --check`
- `PYTHONPATH=src python -m lrh.cli.main validate`

# Follow-up

- Expand list rendering to source `setup_checked_as_of` and `checkout_storage` from persisted resolver-backed state instead of placeholders.
