---
resolution: null
blocked_reason: null
blocked: false
id: WI-WORKSTREAM-SNAPSHOT-MVP
title: Summarize workstream lifecycle state in snapshots
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
  - WI-WORKSTREAM-PLANNING-TREE-RELATIONSHIPS-MVP
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - snapshots include proposed/active/resolved/abandoned workstream summary
required_evidence:
  - test_result
artifacts_expected:
  - code_diff
  - test_module
---

## Summary

Extend snapshot output to summarize workstream lifecycle status as a first-class
project-control view.

## Safe-default alignment

Snapshot visibility is observability only and must not imply execution, scheduling, or agent invocation.
