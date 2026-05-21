---
execution_id: 2026_05_21_20_15_22_SERVE_OPERATIONAL_FIELDS_UX_ORDERING
prompt_id: PROMPT(AD_HOC:SERVE_OPERATIONAL_FIELDS_UX_ORDERING)[2026-05-19T14:20:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-21T20:15:22+00:00
---

# Summary

Populate available serve operational facts from shared APIs and improve UX ordering so project identity, primary triage facts, and next useful actions appear before diagnostics.

# Result

- Added setup-guidance rendering for remote-only cards and dashboards, and reordered dashboard sections to emphasize triage-first content.
- Preserved unsupported fields as explicit capability gaps and kept safe-default read-only behavior.
- Addressed review follow-up by shell-quoting registry names in setup guidance and avoiding double-escaping.
- Normalized unknown validation counts in project dashboards to render as `Unknown / not implemented` instead of `None`.

# Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`

# Follow-up

- Populate additional key source links and richer readiness/design details as shared APIs expose stable typed fields for those facts.
