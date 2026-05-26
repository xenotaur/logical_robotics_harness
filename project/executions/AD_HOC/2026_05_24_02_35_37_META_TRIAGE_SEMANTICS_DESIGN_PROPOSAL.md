---
execution_id: 2026_05_24_02_35_37_META_TRIAGE_SEMANTICS_DESIGN_PROPOSAL
prompt_id: PROMPT(AD_HOC:META_TRIAGE_SEMANTICS_DESIGN_PROPOSAL)[2026-05-23T15:00:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/308
commit: fee2a2c
created_at: 2026-05-24T02:35:37+00:00
---

# Summary

Recorded a companion semantics proposal for the LRH meta operational triage
dashboard, focused on action-oriented lane semantics, deterministic
classification precedence, evidence contracts, suggested actions, and vocabulary
migration.

# Result

- Added `project/design/proposals/proposed/meta-operational-triage-semantics/`
  with an umbrella proposal and proposal-set README.
- Updated proposal indexes and the existing
  `lrh-serve-operational-triage-mvp` proposal-set README with a companion link.

# Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/test`
- `scripts/lint`
- `scripts/format --check`

# Follow-up

- Implement semantics in small, follow-on runtime PRs (classifier updates,
  field/label migration, evidence payload parity, and portfolio-state metadata).
