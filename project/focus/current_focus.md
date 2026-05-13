---
id: FOCUS-WORKSTREAM-CONTROL-PLANE-MVP
title: Plan execution readiness and dry-run contracts for bounded execution
status: active
priority: high
owner: anthony
related_principles:
  - PRINCIPLES-ENGINEERING
  - PRINCIPLES-EVALUATION
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-EXECUTION-FRAMEWORK
---

# Current Focus

The immediate priority is the **bounded agent execution framework planning phase**. This is not a
push to make agents autonomous. The immediate phase is to define and validate execution readiness
and run-packet contracts for selected work items while human approval gates remain in place.

Recently completed:

- landed the Workstream Control Plane MVP baseline for representing, loading, validating,
  snapshotting, organizing, and tidying workstreams
- created the first-class `WS-EXECUTION-FRAMEWORK` workstream
- updated the proposed execution-framework design around bounded branch-level agency, run packets,
  agent-owned branches, pull requests, bounded CI/review stabilization loops, final run reports, and
  human/policy gates

## Why this is active now

LRH now has enough project-control structure to plan the next execution-framework phase without
jumping directly to runtime automation. The next work should make selected work items ready for
future execution by defining readiness metadata, producing dry-run run packets, and producing final
run-report contracts that tie status to evidence.

## First implementation slice

The first implementation package after this planning PR should include only:

1. `WI-EXECUTION-READINESS-SCHEMA`
2. `WI-RUN-PACKET-DRY-RUN`
3. `WI-RUN-REPORT-MVP`

This package should define the fields, generated artifacts, evidence expectations, and human review
steps needed before any branch mutation, agent backend, or stabilization loop can be implemented.

## Human and policy gates

Execution-framework planning must preserve explicit human/policy gates for:

- approving a work item as execution-ready
- approving generated run packets before mutation-capable work
- reviewing validation evidence and final run reports
- merging pull requests
- release or publish decisions
- closing out work items and workstreams

## Non-Goals

- Implementing runtime code, CLI behavior, schema validation, GitHub API integration, or tests for
  runtime execution behavior in this planning PR.
- Adding `lrh run` or any autonomous run command.
- Invoking coding agents, mutating branches, or adding execution backends.
- Implementing PR stabilization loops, CI response automation, or merge/publish automation.
- Adding MCP bridges, telemetry systems, privileged workflow execution, or secrets-management
  behavior beyond documented policy assumptions.

## Exit Criteria

This focus is complete when:

1. the roadmap clearly stages the bounded execution-framework phase
2. the execution-framework workstream points at the first implementation sequence
3. work items exist for execution readiness, run packet dry-run, run report MVP, branch containment,
   PR/CI observation, and bounded stabilization-loop design
4. the first implementation prompt package can safely start with readiness, dry-run packets, and run
   reports without backend or branch-mutation work
