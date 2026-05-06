---
resolution: null
blocked_reason: null
blocked: false
id: WI-PLANNING-NODE-SCHEMA-MVP
title: Define planning-node schema semantics
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
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - planning-node fields such as `parent_id` and `children` are documented
  - schema wording is core LRH control-plane behavior and does not imply autonomous execution
required_evidence:
  - manual_review
artifacts_expected:
  - code_diff
  - documentation
---

## Summary

Define the documentation-level planning-node schema that lets projects, workstreams, and work items participate in recursive planning relationships.

## Safe-default alignment

This work item is planning/control-plane work only. It must function without `lrh[agentic]`, must
not add autonomous execution behavior, and must preserve human-assisted operation as the default.
