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

The immediate priority is **safe-default execution-framework alignment**: keep prerequisite control-plane interpretation separate from the first execution-contract package, then define execution readiness, dry-run run packets, and run reports for selected or explicitly opted-in work items. Human approval gates remain in place, and `lrh serve`, autonomous dispatch, branch mutation, PR creation, stabilization loops, and merge/publish automation stay outside the first package.

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

The first execution-contract implementation package after this planning PR should be:

1. `WI-EXECUTION-READINESS-SCHEMA`
2. `WI-RUN-PACKET-DRY-RUN`
3. `WI-RUN-REPORT-MVP`

This package should define the fields, generated artifacts, evidence expectations, and human review
steps needed before any branch mutation, agent backend, or stabilization loop can be implemented.
Shared core state APIs, planning relationship validation, and snapshot-visible planning summaries are
prerequisite control-plane alignment, not part of the first execution-contract package. If a future
prompt discovers one of those prerequisites is missing, it should stop and create a separate
prerequisite prompt before starting the package above. The safe-default `lrh serve` viewer/prompt
workbench is a later read-only/local-assist package and should consume these contracts rather than
blocking or broadening the first package.

## Adjacent CI capability design

The CI capability scaffolding workstream
(`project/workstreams/proposed/WS-CI-CAPABILITY-SCAFFOLDING.md`) is a proposed adjacent
design/control-plane effort for reusing LRH's CI and toolchain reconciliation
lessons. It should remain playbook- and prompt-design work for now, not CI workflow implementation or
a universal template effort.

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
2. the execution-framework workstream points at the first execution-contract implementation package
3. work items exist for shared core state APIs, planning relationship validation, snapshot-visible
   planning summaries, safe-default `lrh serve`, execution readiness, run packet dry-run, run report
   MVP, branch containment, PR/CI observation, and bounded stabilization-loop design
4. the first execution-contract prompt package can safely start with
   `WI-EXECUTION-READINESS-SCHEMA`, `WI-RUN-PACKET-DRY-RUN`, and `WI-RUN-REPORT-MVP` after prerequisite
   control-plane alignment is verified
