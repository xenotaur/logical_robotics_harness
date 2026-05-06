---
resolution: null
blocked_reason: null
blocked: false
id: WI-PLANNING-TREE-VALIDATION-RULES-MVP
title: Define planning-tree validation rules
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
blocked_by: []
expected_actions:
  - edit_file
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - cycle detection, missing references, and parent/child consistency rules are specified
  - rules are implementable without agentic dependencies or runtime execution
required_evidence:
  - manual_review
artifacts_expected:
  - code_diff
  - documentation
---

## Summary

Define validation expectations for recursive planning-tree metadata before implementation work begins.

## Safe-default alignment

This work item is planning/control-plane work only. It must function without `lrh[agentic]`, must
not add autonomous execution behavior, and must preserve human-assisted operation as the default.
