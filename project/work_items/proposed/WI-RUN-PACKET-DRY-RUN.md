---
resolution: null
blocked_reason: null
blocked: false
id: WI-RUN-PACKET-DRY-RUN
title: Generate dry-run run packets from execution-ready work items
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-WORKSTREAM-CONTROL-PLANE-MVP
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-EXECUTION-FRAMEWORK
related_design:
  - project/design/proposals/proposed/workstream-execution-framework/00_proposal.md
  - project/design/proposals/adopted/workstreams-and-recursive-planning-tree/00_proposal.md
depends_on:
  - WI-EXECUTION-READINESS-SCHEMA
blocked_by: []
expected_actions:
  - edit_file
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - a dry-run run-packet contract is documented for selected execution-ready work items
  - packet contents include scope, constraints, validation commands, evidence expectations, and human gates
  - dry-run behavior explicitly avoids agent calls and branch mutation
  - the work item leaves backend adapters and PR automation out of scope
required_evidence:
  - manual_review
artifacts_expected:
  - documentation
---

## Summary

Generate a run packet from a selected execution-ready work item without calling an agent or mutating a branch.

## Problem / Context

Run packets are the bridge from project-control planning to bounded execution. The first slice must prove packet content and reviewability in dry-run/manual mode before LRH adds branch mutation, backend adapters, or stabilization loops.

## Required Changes

- Define a Markdown run-packet shape that captures selected work item scope, constraints, allowed/forbidden paths, validation commands, evidence expectations, and human approval state.
- Plan dry-run generation behavior that writes or previews artifacts without invoking agents, creating branches, opening pull requests, or changing repository state outside the intended output.
- Document how packet generation reports missing readiness fields and review tasks.
- Keep any command naming provisional and avoid committing to autonomous `lrh run` behavior.

## Non-Goals

- Do not implement runtime code, CLI behavior, schema validation, GitHub API integration, agent execution, execution backends, orchestration, or `lrh run` behavior as part of this planning/design item.
- Do not add automatic merge, release/publish automation, privileged workflow execution, MCP bridges, telemetry systems, or full autonomous execution.

## Acceptance Criteria

- a dry-run run-packet contract is documented for selected execution-ready work items
- packet contents include scope, constraints, validation commands, evidence expectations, and human gates
- dry-run behavior explicitly avoids agent calls and branch mutation
- the work item leaves backend adapters and PR automation out of scope

## Validation Commands

- `scripts/version tools`
- `lrh validate`
- `scripts/test` when the implementation change touches package behavior or validation logic

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-EXECUTION-FRAMEWORK.md`
- Proposed execution-framework proposal: `project/design/proposals/proposed/workstream-execution-framework/00_proposal.md`
- Adopted planning-tree proposal: `project/design/proposals/adopted/workstreams-and-recursive-planning-tree/00_proposal.md`

## Risk Notes

- Packet generation could be mistaken for permission to execute automatically.
- Packet contents could duplicate work-item data without preserving explicit constraints.

## Dependencies / Order

Second in the implementation package after readiness fields are defined.
