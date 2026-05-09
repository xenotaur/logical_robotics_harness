---
execution_id: 2026_05_07_06_15_43_IMPLEMENT_PLANNING_TREE_RELATIONSHIP_MVP
prompt_id: PROMPT(WI-PLANNING-TREE-RELATIONSHIP-MVP:IMPLEMENT_PLANNING_TREE_RELATIONSHIP_MVP)[2026-05-06T11:10:00-04:00]
work_item: WI-WORKSTREAM-PLANNING-TREE-RELATIONSHIPS-MVP
status: in_progress
rerun_of:
pr: xenotaur/logical_robotics_harness#204
commit: 5aa2cc0bf627ec7282986daaf1e50bdc86da5cc5
created_at: 2026-05-07T06:15:43+00:00
---

# Summary

Implemented the Planning-Tree Relationship MVP as a focused internal control-plane relationship
slice for workstreams and work items.

# Result

Added a reusable planning-tree relationship index that treats workstreams as planning nodes and work
items as executable leaves. The index resolves `parent_id`, `children`, and `work_items` metadata by
ID rather than by path, exposes roots, children, parents, unresolved-reference diagnostics, and cycle
information, and keeps path/nested-directory placement non-semantic.

Integrated relationship diagnostics into validation for unknown `parent_id`, unknown child IDs,
duplicate IDs across relationship-indexed workstreams and work items, simple cycles among
workstream planning nodes, and conservative parent/child mismatch warnings. Work item `parent_id`
is now tolerated as an optional parent-workstream relationship field.

Added focused tests for workstream-to-work-item relationships, workstream-to-workstream
relationships, parent-id and children-derived relationships, missing references, cycles, duplicate
relationship IDs, mismatch warnings, ignored README/placeholder files, and avoiding path-derived
relationships. Updated workstream and schema documentation to describe the implemented relationship
indexing behavior.

# Validation

- `scripts/version tools` passed and confirmed expected Ruff/Black tool versions were available.
- `python -m unittest tests.workstreams_tests.planning_tree_test tests.workstreams_tests.loader_test tests.workstreams_tests.validator_test tests.control_tests.loader_test tests.control_tests.validator_test` passed.
- `scripts/test` passed.
- `lrh validate --project-dir project` passed.
- `scripts/lint` passed.
- `scripts/format --check` passed.
- Review follow-up adjusted `work_items` kind checking, multiple-parent warning deduplication, work-item `parent_id` schema nullability, and execution-record status metadata.
- Review follow-up validation ran `scripts/version tools`, `scripts/format --check --diff`, `scripts/lint`, `scripts/test`, and `lrh validate --project-dir project`; all passed after applying repository formatting.

# Follow-up

Pause and review this Planning-Tree Relationship MVP before generating or running the Snapshot MVP
and Organize/Tidy MVP prompts. Snapshot output, organize/tidy behavior, automation, agent execution,
execution backends, orchestration, and `lrh run` remain deferred.
