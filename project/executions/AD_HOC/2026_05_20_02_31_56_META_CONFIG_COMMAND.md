---
execution_id: 2026_05_20_02_31_56_META_CONFIG_COMMAND
prompt_id: PROMPT(AD_HOC:META_CONFIG_COMMAND)[2026-05-19T13:55:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-20T02:31:56+00:00
---

# Summary

Implemented `lrh meta config` commands (`list/get/set/unset`) for the trusted persistent local-state setting, integrated config reads into storage policy resolution, surfaced setting visibility in `lrh meta where`, and added focused tests/docs for the new configuration flow.

# Result

Completed and committed changes in commit `e514c29` for PR #288. Added CLI + workspace config logic, docs updates, and `tests/meta_tests/config_test.py` coverage. This record was generated for prompt `PROMPT(AD_HOC:META_CONFIG_COMMAND)[2026-05-19T13:55:00-04:00]`.

# Validation

- `scripts/version tools`
- `scripts/test tests/meta_tests/config_test.py tests/meta_tests/where_test.py`
- `scripts/lint`
- `scripts/format --check`
- `PYTHONPATH=src python -m lrh.cli.main validate`

# Follow-up

- Follow-up meta/serve sequence steps can consume this setting when wiring trusted workspace persistence into additional command surfaces.
