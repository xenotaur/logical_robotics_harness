---
resolution: null
blocked_reason: null
blocked: false
id: WI-AGENTIC-CAPABILITY-DEFERRAL-MVP
title: Record deferred agentic capability backlog
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
  - future `lrh agentic run` / `lrh-agentic run`, agent adapters, PR stabilization loops, and sandbox envelope work are listed
  - `lrh run` legacy shorthand or aliasing questions are documented for future command-design resolution
  - all entries are clearly marked deferred / future / requires `lrh[agentic]`
required_evidence:
  - manual_review
artifacts_expected:
  - code_diff
  - documentation
---

## Summary

Record the explicit future-agentic backlog so planning-tree work remains safe-default and non-agentic
by default. This should also clarify that older `lrh run` references are legacy shorthand until a
future command-design decision resolves omission, non-agentic preparation semantics, or
installed-agentic aliasing.

## Safe-default alignment

This work item is planning/control-plane work only. It must function without `lrh[agentic]`, must
not add autonomous execution behavior, and must preserve human-assisted operation as the default.
