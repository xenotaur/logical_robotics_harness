---
id: FOCUS-EXECUTION-FRAMEWORK-PLANNING
title: Align Layer 2 durable run state after safe-default serve closeout
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

The immediate priority is **Layer 2 durable run state/manual run tracking alignment** after safe-default execution-framework closeout: the prerequisite control-plane interpretation work, first execution-contract package, and safe-default `lrh serve` local viewer / prompt workbench are implemented. Human approval gates remain in place, and observation adapters, autonomous dispatch, branch mutation, PR creation, stabilization loops, and merge/publish automation remain outside the next package.

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
- implemented the safe-default `lrh serve` local server skeleton, read-only project/workstream/work-item
  viewer, and prompt/run-packet/report workbench

## Why this is active now

LRH now has enough project-control structure to plan durable manual run state without jumping
directly to observation or runtime automation. Shared APIs, planning relationship validation,
snapshot-visible summaries, opt-in readiness metadata, dry-run packet rendering, report rendering, and
the local human-assist surface are in place.

## Next implementation slice

The next implementation package should be **Layer 2: durable run state/manual run tracking**. It
should define manual-mode run artifacts such as `project/runs/<RUN-ID>/`, `packet.yaml`,
`state.yaml`, `events.jsonl`, `prompts/`, `evidence/`, `report.md`, manual lifecycle states,
explicit-click/manual update paths, and parity between manual runs and future automated runs. It
should not add observation adapters, branch containment, autonomous dispatch, branch mutation, PR
creation, stabilization loops, merge/release automation, or backend adapters.

## Next implementation package

The next package is **Layer 2: durable run state/manual run tracking**. It should identify the
`project/runs/<RUN-ID>/` layout, `packet.yaml`, `state.yaml`, `events.jsonl`, prompts, evidence,
`report.md`, manual-mode run lifecycle states, explicit-click/manual update paths, and parity between
manual runs and future automated runs. It should not implement observation adapters, branch
containment, stabilization loops, backend adapters, agent dispatch, branch mutation, PR creation,
merge/release automation, or destructive actions.

## Supporting Design Work

- The LRH Serve Operational Triage MVP design proposal defines a meta-aware, operational,
  safe-default, state-aware triage extension viewer for `lrh serve`. As the viewer sprint is
  completed and carried forward, this design is intended to help LRH and other registered
  LRH-managed projects inspect validation state, current focus, design/workstream/work-item
  traceability, readiness, and prompt-generation affordances so humans can choose the next safe
  prompt-driven action more quickly.

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

- Implementing observation adapters, branch containment, runtime automation, GitHub API integration,
  or tests for mutation-capable runtime execution behavior in the next Layer 2 planning/implementation package.
- Adding `lrh run` or any autonomous run command beyond safe-default design references.
- Invoking coding agents, mutating branches, opening PRs automatically, or adding execution backends.
- Implementing PR stabilization loops, CI response automation, or merge/publish automation.
- Adding MCP bridges, telemetry systems, privileged workflow execution, or secrets-management
  behavior beyond documented policy assumptions.

## Exit Criteria

This focus is complete when:

1. the roadmap clearly stages the bounded execution-framework phase
2. the execution-framework workstream identifies Layer 2 durable run state/manual run tracking as the
   next implementation package
3. the completed safe-default `lrh serve` viewer / prompt workbench package is resolved with
   evidence-backed closeout
4. later observation, branch containment, stabilization-loop, backend-adapter, branch-mutation,
   PR-creation, merge/release automation, and destructive-operation work remains deferred
