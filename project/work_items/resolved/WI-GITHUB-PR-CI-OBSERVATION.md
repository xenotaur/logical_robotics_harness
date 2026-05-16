---
resolution: Resolved as design-level planning by the execution-framework Layer 3 observation-adapter boundary, which documents read-only PR/CI/review observation and defers mutation/backends; semantic audit evidence is recorded in project/evidence/EV-0010.md.
blocked_reason: null
blocked: false
id: WI-GITHUB-PR-CI-OBSERVATION
title: Design GitHub PR and CI observation adapter
type: deliverable
status: resolved
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
  - WI-AGENT-BRANCH-CONTAINMENT
blocked_by: []
expected_actions:
  - edit_file
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - read-only PR/review/CI observation boundaries are documented
  - mutation operations are explicitly out of scope
  - observed state maps to run-report evidence needs
  - backend/API implementation is deferred until contracts are stable
required_evidence:
  - manual_review
artifacts_expected:
  - documentation
---

## Summary

Read PR, review, and CI status without mutating repository state.

## Problem / Context

Bounded stabilization needs reliable observation before response automation. The first GitHub-facing work should be read-only and evidence-oriented, not mutation-capable.

## Required Changes

- Define read-only adapter boundaries for PR metadata, review state, and CI status.
- Document authentication and permission assumptions at the policy level without implementing secrets management.
- Describe evidence outputs that can feed run reports.
- Explicitly defer commenting, pushing, rerunning workflows, merging, and closing PRs.

## Non-Goals

- Do not implement runtime code, CLI behavior, schema validation, GitHub API integration, agent execution, execution backends, orchestration, or `lrh run` behavior as part of this planning/design item.
- Do not add automatic merge, release/publish automation, privileged workflow execution, MCP bridges, telemetry systems, or full autonomous execution.

## Acceptance Criteria

- read-only PR/review/CI observation boundaries are documented
- mutation operations are explicitly out of scope
- observed state maps to run-report evidence needs
- backend/API implementation is deferred until contracts are stable

## Validation Commands

- `scripts/version tools`
- `lrh validate`
- `scripts/test` when the implementation change touches package behavior or validation logic

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-EXECUTION-FRAMEWORK.md`
- Proposed execution-framework proposal: `project/design/proposals/proposed/workstream-execution-framework/00_proposal.md`
- Adopted planning-tree proposal: `project/design/proposals/adopted/workstreams-and-recursive-planning-tree/00_proposal.md`

## Risk Notes

- Observation work could expand into GitHub mutation APIs too early.
- Permission assumptions could become hidden dependencies.

## Dependencies / Order

After branch containment policy support and before stabilization-loop implementation.
