---
execution_id: 2026_05_14_00_16_48_IMPLEMENT_CORE_STATE_APIS_MVP
prompt_id: PROMPT(WI-LRH-CORE-STATE-APIS-MVP:IMPLEMENT_CORE_STATE_APIS_MVP)[2026-05-13T19:34:00-04:00]
work_item: WI-LRH-CORE-STATE-APIS-MVP
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-14T00:16:48+00:00
---

# Summary

Implemented the shared core state API MVP as a read-only typed interpretation
layer over the existing project loader, validator, and planning-tree index.

# Result

Added `lrh.core_state.load_core_project_state()` with typed summaries for
project identity, current focus, validation/readiness, workstreams, work items,
parent/child planning relationships, active leaf work items, evidence links, and
prompt-rendering inputs. Added unit coverage for representative project loading,
deterministic ordering, source/frontmatter boundary preservation, and incomplete
optional planning relationships.

# Validation

- `scripts/version tools` passed; Ruff and Black were available.
- `scripts/format --check --diff` passed.
- `scripts/lint` passed.
- `scripts/test` passed.
- `lrh validate` passed.

# Follow-up

Use the new core state API from later planning-tree validation, snapshot, and
execution-contract work. The next prompt `WI-PLANNING-TREE-VALIDATION-RULES-MVP`
is unblocked from the shared-state API perspective.
