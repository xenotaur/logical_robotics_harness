---
id: FOCUS-EXECUTION-FRAMEWORK-PLANNING
title: Advance safe-default serve viewer after execution contracts
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

The immediate priority is **safe-default execution-framework closeout and next-package alignment**: the prerequisite control-plane interpretation work and first execution-contract package are implemented, so the next package is the safe-default `lrh serve` local viewer / prompt workbench. Human approval gates remain in place, and autonomous dispatch, branch mutation, PR creation, stabilization loops, and merge/publish automation stay outside the next package.

Canonical living design/context package: `project/design/execution_framework_mvp.md`.

Recently completed:

- landed the Workstream Control Plane MVP baseline for representing, loading, validating,
  snapshotting, organizing, and tidying workstreams
- created the first-class `WS-EXECUTION-FRAMEWORK` workstream
- updated the execution-framework design to prioritize a safe-default local `lrh serve` viewer and
  prompt workbench before durable run artifacts, observation adapters, or optional agentic execution
- implemented the shared core-state APIs, planning relationship validation/indexing, and
  snapshot-visible planning summaries needed by later execution-framework surfaces
- implemented the opt-in execution-readiness schema, safe-default dry-run run-packet renderer, and
  safe-default run-report renderer

## Why this is active now

LRH now has enough project-control structure to start the next execution-framework package without
jumping directly to runtime automation. Shared APIs, planning relationship validation,
snapshot-visible summaries, opt-in readiness metadata, dry-run packet rendering, and report rendering
are in place; the next work should expose those capabilities through a local human-assist surface.

## Next implementation slice

The next implementation package should be `WI-LRH-SERVE-SAFE-DEFAULT-MVP` as a local read-only
viewer / prompt workbench that consumes the completed shared state, execution-readiness, run-packet,
and run-report contracts. Its selected sequence is: plan/control-plane refinement; local server
skeleton; read-only project/workstream/work-item viewer; and prompt/run-packet/report workbench MVP.
The next implementation prompt after planning should implement only the local server skeleton without
autonomous dispatch, branch mutation, PR creation, stabilization loops, merge/release automation, or
backend adapters.

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
4. the safe-default `lrh serve` viewer / prompt workbench package is staged into plan refinement,
   local server skeleton, read-only viewer, and prompt/run-packet/report workbench slices
