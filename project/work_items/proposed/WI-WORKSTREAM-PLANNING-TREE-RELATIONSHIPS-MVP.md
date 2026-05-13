---
resolution: null
blocked_reason: null
blocked: false
id: WI-WORKSTREAM-PLANNING-TREE-RELATIONSHIPS-MVP
title: Validate metadata-driven planning-tree relationships
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-WORKSTREAM-CONTROL-PLANE-MVP
related_roadmap:
  - ROADMAP-PHASE-01
  - ROADMAP-PHASE-01A
depends_on:
  - WI-WORKSTREAM-VALIDATION-MVP
  - WI-PLANNING-TREE-VALIDATION-RULES-MVP
  - WI-WORKSTREAM-WORK-ITEM-RELATIONSHIPS-MVP
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - parent/child references are validated via metadata
  - the relationship/index model can resolve projects, workstreams, work items, active leaves, readiness/status summaries, and evidence/status links
  - path-derived relationship assumptions are avoided
required_evidence:
  - test_result
artifacts_expected:
  - code_diff
  - test_module
---

## Summary

Add or prepare planning-tree relationship validation for workstreams and work items,
anchored in metadata references rather than filesystem nesting. The shared model should preserve the
user-facing `Project -> Workstream -> Work Item` vocabulary while giving CLI, snapshot, request,
serve, and future run surfaces one reusable relationship/index.

## Safe-default alignment

This implementation slice should follow the design rules from `WI-PLANNING-TREE-VALIDATION-RULES-MVP` and `WI-WORKSTREAM-WORK-ITEM-RELATIONSHIPS-MVP`.
