---
execution_id: 2026_05_20_06_42_06_ACTIVITY_LANES_OBSERVATIONAL_DASHBOARD_PROPOSAL
prompt_id: PROMPT(AD_HOC:ACTIVITY_LANES_OBSERVATIONAL_DASHBOARD_PROPOSAL)[2026-05-17T00:00:00+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-20T06:42:06+00:00
---

# Summary

Added a focused design-proposal document for a tool-agnostic activity-lane and observational-dashboard architecture, plus a minimal proposals README entry for discoverability.

# Result

Created `project/design/proposals/proposed/activity-lanes-and-observational-dashboard.md` with the requested 18 sections and explicit local-first/read-only MVP boundaries; updated `project/design/proposals/README.md`; validated with repository CLI checks.

# Validation

- `scripts/version tools`
- `lrh validate` (0 errors, 0 warnings)

# Follow-up

Runtime implementation remains deferred to follow-on work (lane schema/parser, adapters, snapshot interpreter, and `lrh serve` wiring).
