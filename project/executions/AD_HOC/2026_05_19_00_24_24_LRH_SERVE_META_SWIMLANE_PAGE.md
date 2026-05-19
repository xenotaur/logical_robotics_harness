---
execution_id: 2026_05_19_00_24_24_LRH_SERVE_META_SWIMLANE_PAGE
prompt_id: PROMPT(AD_HOC:LRH_SERVE_META_SWIMLANE_PAGE)[2026-05-18T17:10:00-04:00]
work_item: AD_HOC
status: planned
rerun_of: 
pr: 
commit: 
created_at: 2026-05-19T00:24:24+00:00
---

# Summary

Add a safe-default, read-only `lrh serve` meta swimlane page for registered
projects, aligned with the proposed operational triage MVP.

# Result

Implemented `/meta`, `/meta/project`, and `/api/meta` surfaces that group
registered projects into deterministic operational lanes using the shared UX
view-model contract. Per-project registry failures are isolated into unavailable
cards, dynamic HTML is escaped, and unavailable/not-implemented fields are shown
as explicit capability gaps rather than hidden.

# Validation

- `scripts/version tools`
- `scripts/format --check`
- `scripts/lint`
- `scripts/test`
- `python -m lrh.cli.main validate`

# Follow-up

Future work should replace placeholder capability gaps with shared APIs for
cached source state, detailed project inspectors, and adopted-but-not-implemented
design counts when those contracts are available.
