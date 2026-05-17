---
resolution: completed
blocked_reason: null
blocked: false
id: WI-WORKSTREAM-ORGANIZE-TIDY-MVP
title: Add dry-run-first organize/tidy support for workstreams
type: operation
status: resolved
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
  - WI-WORKSTREAM-SNAPSHOT-MVP
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - organize/tidy support is dry-run-first
  - organization behavior respects metadata authority
required_evidence:
  - test_result
artifacts_expected:
  - code_diff
  - test_module
---

## Summary

Add optional organize/tidy behavior for workstreams after validation is stable,
starting with dry-run-first operations.

## Safe-default alignment

Organize/tidy behavior must remain dry-run-first and non-agentic.
