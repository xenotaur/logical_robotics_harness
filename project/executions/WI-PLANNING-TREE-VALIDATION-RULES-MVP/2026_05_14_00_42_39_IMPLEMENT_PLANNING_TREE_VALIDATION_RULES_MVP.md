---
execution_id: 2026_05_14_00_42_39_IMPLEMENT_PLANNING_TREE_VALIDATION_RULES_MVP
prompt_id: PROMPT(WI-PLANNING-TREE-VALIDATION-RULES-MVP:IMPLEMENT_PLANNING_TREE_VALIDATION_RULES_MVP)[2026-05-13T19:35:00-04:00]
work_item: WI-PLANNING-TREE-VALIDATION-RULES-MVP
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-14T00:42:39+00:00
---

# Summary

Implemented the focused MVP planning-tree validation layer for recursive workstream/work-item
metadata. The change stays in the control-plane validator/index path and does not add runtime
execution, scheduling, agentic behavior, branch mutation, or serve/run authority.

# Result

Added deterministic diagnostics for self-parenting, active orphaned work-item leaves, and active
workstreams that have no active/proposed work-item leaf. Existing diagnostics already covered
duplicate planning IDs, invalid workstream `kind`, unknown parent references, unknown child
references, work-item child kind errors, cycles, and parent/child disagreement; tests were expanded
to lock down the MVP rule set. Documentation now describes implemented rules and notes that explicit
top-level markers for active workstreams are not in the schema yet, so root active workstream orphan
validation is deferred.

# Validation

- `scripts/version tools` passed; Black/Ruff versions were available.
- `scripts/format --check --diff` initially reported one test-file formatting diff after editing; `scripts/format` reformatted it.
- `scripts/format --check --diff` passed after formatting.
- `scripts/lint` initially reported two E501 line-length issues in `src/lrh/control/planning_tree.py`; the lines were wrapped.
- `scripts/lint` passed after wrapping.
- `scripts/test` passed: 450 tests.
- `lrh validate` passed with 0 errors and 3 warnings for pre-existing active work items that are not attached to planning parents.

# Follow-up

- Add explicit schema semantics for intentional top-level active workstreams before warning on every
  root active workstream as an orphan.
- `WI-WORKSTREAM-PLANNING-TREE-RELATIONSHIPS-MVP` is unblocked for broader relationship indexing on
  top of the deterministic validation behavior.
