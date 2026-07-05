---
resolution: null
blocked_reason: null
blocked: false
id: WI-AGENT-BRANCH-CONTAINMENT
title: Document agent branch containment policy support
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-EXECUTION-FRAMEWORK
related_design:
  - project/design/proposals/proposed/workstream-execution-framework/00_proposal.md
  - project/design/proposals/adopted/workstreams-and-recursive-planning-tree/00_proposal.md
depends_on:
  - WI-RUN-PACKET-DRY-RUN
  - WI-RUN-REPORT-MVP
blocked_by: []
expected_actions:
  - edit_file
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - branch namespace and protected-gate assumptions are documented
  - future mutation-capable behavior is constrained by policy/config prerequisites
  - automatic merge and publish automation remain explicitly deferred
  - the work item does not implement branch mutation
required_evidence:
  - manual_review
artifacts_expected:
  - documentation
---

## Summary

Document and prepare internal policy/config support for agent-owned branch namespaces and protected merge gates.

## Problem / Context

Future execution may use agent-owned branches and pull requests, but branch mutation must be planned behind explicit containment policies. This design support should come after packet and report contracts exist.

## Scope

- Document branch namespace conventions and protected merge-gate
  assumptions for future agent-owned branches.
- Identify the policy/config fields required before any mutation-capable
  branch behavior is implemented.
- Explicitly defer automatic merge, release/publish automation, and
  privileged workflow execution as non-goals.

## Required Changes

- Document branch namespace conventions for future agent-owned branches.
- Define protected merge-gate assumptions and required human approvals.
- Identify policy/config fields needed before any mutation-capable branch behavior is implemented.
- Record non-goals for automatic merge, release/publish automation, privileged workflows, and secret mutation.

## Non-Goals

- Do not implement runtime code, CLI behavior, schema validation, GitHub API integration, agent execution, execution backends, orchestration, or `lrh run` behavior as part of this planning/design item.
- Do not add automatic merge, release/publish automation, privileged workflow execution, MCP bridges, telemetry systems, or full autonomous execution.

## Acceptance Criteria

- branch namespace and protected-gate assumptions are documented
- future mutation-capable behavior is constrained by policy/config prerequisites
- automatic merge and publish automation remain explicitly deferred
- the work item does not implement branch mutation

## Validation

- `scripts/version tools`
- `lrh validate`

Also run `scripts/test` if the implementation touches package behavior or
validation logic.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-EXECUTION-FRAMEWORK.md`
- Proposed execution-framework proposal: `project/design/proposals/proposed/workstream-execution-framework/00_proposal.md`
- Adopted planning-tree proposal: `project/design/proposals/adopted/workstreams-and-recursive-planning-tree/00_proposal.md`

## Risk Notes

- Prematurely normalizing branch mutation before readiness gates are enforced.
- Leaving protected-branch and permission assumptions implicit.

## Dependencies / Order

After the first implementation package. It prepares policy support only.
