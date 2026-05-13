---
id: FOCUS-EXECUTION-FRAMEWORK-PLANNING
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

The immediate priority is **safe-default execution-framework alignment**: shared core state APIs with planning relationship/index validation, snapshot-visible planning summaries, an early read-only `lrh serve` viewer/prompt workbench, then durable run-state and run-report contracts for selected or explicitly opted-in work items. Human approval gates remain in place, and autonomous dispatch or branch mutation stays outside the default layer.

Canonical living design/context package: `project/design/execution_framework_mvp.md`.

Recently completed:

- landed the Workstream Control Plane MVP baseline for representing, loading, validating,
  snapshotting, organizing, and tidying workstreams
- created the first-class `WS-EXECUTION-FRAMEWORK` workstream
- updated the execution-framework design to prioritize a safe-default local `lrh serve` viewer and
  prompt workbench before durable run artifacts, observation adapters, or optional agentic execution

## Why this is active now

LRH now has enough project-control structure to plan the next execution-framework phase without
jumping directly to runtime automation. The next work should expose existing project/control-plane
state through shared APIs, planning relationship validation, snapshot-visible summaries, and a local
human-assist surface, then make selected or explicitly opted-in work items ready for future execution
by defining readiness metadata, durable run artifacts, and final run-report contracts that tie status
to evidence.

## First implementation slice

The first implementation sequence after this planning PR should be:

1. `WI-LRH-CORE-STATE-APIS-MVP`
2. `WI-WORKSTREAM-PLANNING-TREE-RELATIONSHIPS-MVP` / `WI-PLANNING-TREE-VALIDATION-RULES-MVP`
3. `WI-WORKSTREAM-SNAPSHOT-MVP`
4. `WI-LRH-SERVE-SAFE-DEFAULT-MVP`
5. `WI-EXECUTION-READINESS-SCHEMA`
6. `WI-RUN-PACKET-DRY-RUN`
7. `WI-RUN-REPORT-MVP`

This sequence should expose current state safely and keep CLI/server planning interpretations shared,
then define the fields, generated artifacts,
evidence expectations, and human review steps needed before any branch mutation, agent backend, or
stabilization loop can be implemented.

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
- Adding `lrh run` or any autonomous run command beyond safe-default design references.
- Invoking coding agents, mutating branches, opening PRs automatically, or adding execution backends.
- Implementing PR stabilization loops, CI response automation, or merge/publish automation.
- Adding MCP bridges, telemetry systems, privileged workflow execution, or secrets-management
  behavior beyond documented policy assumptions.

## Exit Criteria

This focus is complete when:

1. the roadmap clearly stages the bounded execution-framework phase
2. the execution-framework workstream points at the first implementation sequence
3. work items exist for shared core state APIs, planning relationship validation, snapshot-visible
   planning summaries, safe-default `lrh serve`, execution readiness, run packet dry-run, run report
   MVP, branch containment, PR/CI observation, and bounded stabilization-loop design
4. the first implementation prompt package can safely start with `WI-LRH-CORE-STATE-APIS-MVP`,
   planning relationship validation, `WI-WORKSTREAM-SNAPSHOT-MVP`, `WI-LRH-SERVE-SAFE-DEFAULT-MVP`,
   readiness, dry-run packets, and run reports without backend or branch-mutation work
