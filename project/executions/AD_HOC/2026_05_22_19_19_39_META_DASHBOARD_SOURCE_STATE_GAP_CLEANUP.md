---
execution_id: 2026_05_22_19_19_39_META_DASHBOARD_SOURCE_STATE_GAP_CLEANUP
prompt_id: PROMPT(AD_HOC:META_DASHBOARD_SOURCE_STATE_GAP_CLEANUP)[2026-05-22T10:00:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit: 0827d0a
created_at: 2026-05-22T19:19:39+00:00
---

# Summary

Removed stale source-state capability-gap messaging from meta dashboard project cards so resolved source states do not also claim `source_state` is not implemented.

# Result

- Dropped the default `source_state: not_implemented` capability gap from operational-card construction.
- Added a narrower fallback `source_state_detail: not_implemented` gap only when source-state inspection details are unavailable.
- Added regression checks for `live` and `needs_local_checkout` cards to ensure stale source-state gap text is absent while remote-only setup guidance remains present.

# Validation

- `scripts/version tools`
- `scripts/test`
- `scripts/lint`
- `scripts/format --check`

# Follow-up

- Track broader setup-state versus source-state dashboard semantics in the separate validation/dashboard design pass.
