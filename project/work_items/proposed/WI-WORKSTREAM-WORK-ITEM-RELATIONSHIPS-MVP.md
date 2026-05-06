---
resolution: null
blocked_reason: null
blocked: false
id: WI-WORKSTREAM-WORK-ITEM-RELATIONSHIPS-MVP
title: Define workstream to work item relationships
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-WORKSTREAM-CONTROL-PLANE-MVP
related_roadmap:
  - ROADMAP-PHASE-01A
depends_on:
  - WI-PLANNING-NODE-SCHEMA-MVP
  - WI-WORKSTREAM-SCHEMA-MVP
blocked_by: []
expected_actions:
  - edit_file
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - relationship conventions between workstreams and child work items are documented
  - relationship conventions remain compatible with recursive planning-tree semantics
required_evidence:
  - manual_review
artifacts_expected:
  - code_diff
  - documentation
---

## Summary

Define how workstreams organize work items through metadata without relying on path nesting as authority.

## Safe-default alignment

This work item is planning/control-plane work only. It must function without `lrh[agentic]`, must
not add autonomous execution behavior, and must preserve human-assisted operation as the default.
