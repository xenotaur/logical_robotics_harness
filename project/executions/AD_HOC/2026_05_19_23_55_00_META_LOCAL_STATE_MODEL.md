---
execution_id: 2026_05_19_23_55_00_META_LOCAL_STATE_MODEL
prompt_id: PROMPT(AD_HOC:META_LOCAL_STATE_MODEL)[2026-05-19T13:50:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-05-19T23:55:00+00:00
---

# Summary

Added a typed shared meta local-state model for project identity resolution, checkout bindings,
observation checks, and storage policy defaults to support the meta/serve local-state MVP sequence.

# Result

Implemented `lrh.meta.local_state_model` with resolver precedence for runtime override, private binding,
trusted binding, local-path locator fallback, and URL remote-only fallback; added focused unit tests.

# Validation

- `scripts/version tools`
- `scripts/test`
- `scripts/lint`
- `scripts/format --check`
- `lrh validate`

# Follow-up

- Integrate private/trusted checkout and observation persistence wiring into `meta set/refresh` flows.
- Adopt resolved context model in `meta inspect` and `serve` read paths.
