---
resolution: null
blocked_reason: null
blocked: false
id: WI-RUN-REPORT-MVP
title: Define and generate final run report MVP
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
  - WI-RUN-PACKET-DRY-RUN
blocked_by: []
expected_actions:
  - edit_file
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - run-report fields are documented in a human-readable Markdown contract
  - reports ground status in validation results and evidence references
  - reports include human verification and closeout tasks
  - the MVP does not implement autonomous execution, CI response loops, or merge automation
required_evidence:
  - manual_review
artifacts_expected:
  - documentation
---

## Summary

Define and generate a final Markdown run report with status, evidence, validation results, human verification tasks, and recommended next actions.

## Problem / Context

Execution status must remain evidence-backed. Before LRH can automate branch-contained work or stabilization loops, it needs a minimal report contract that captures what happened, which validations ran, what evidence exists, and what humans must verify next.

## Required Changes

- Define a final Markdown run-report shape for manual or dry-run execution outcomes.
- Include status, linked work item, linked run packet, validation results, evidence references, human verification tasks, policy-gate state, and recommended next actions.
- Describe report behavior for success, blocked, failed, and requires-human-review outcomes.
- Document how run reports should relate to existing execution records without replacing prompt-execution traceability.

## Non-Goals

- Do not implement runtime code, CLI behavior, schema validation, GitHub API integration, agent execution, execution backends, orchestration, or `lrh run` behavior as part of this planning/design item.
- Do not add automatic merge, release/publish automation, privileged workflow execution, MCP bridges, telemetry systems, or full autonomous execution.

## Acceptance Criteria

- run-report fields are documented in a human-readable Markdown contract
- reports ground status in validation results and evidence references
- reports include human verification and closeout tasks
- the MVP does not implement autonomous execution, CI response loops, or merge automation

## Validation Commands

- `scripts/version tools`
- `lrh validate`
- `scripts/test` when the implementation change touches package behavior or validation logic

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-EXECUTION-FRAMEWORK.md`
- Proposed execution-framework proposal: `project/design/proposals/proposed/workstream-execution-framework/00_proposal.md`
- Adopted planning-tree proposal: `project/design/proposals/adopted/workstreams-and-recursive-planning-tree/00_proposal.md`

## Risk Notes

- Reports could become optimistic summaries detached from evidence.
- Reports could be confused with execution records unless the relationship is documented.

## Dependencies / Order

Third in the implementation package after readiness and packet contracts.
