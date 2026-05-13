---
id: WS-EXECUTION-FRAMEWORK
kind: planning_node
title: Safe-Default Execution Framework
status: proposed
stage: planned
origin: follow_up
summary: Define and plan LRH's safe-default execution framework, including a local serve viewer/prompt workbench, run packets, durable run state, observation, and optional later agentic execution.
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
work_items:
  - WI-LRH-CORE-STATE-APIS-MVP
  - WI-WORKSTREAM-PLANNING-TREE-RELATIONSHIPS-MVP
  - WI-PLANNING-TREE-VALIDATION-RULES-MVP
  - WI-WORKSTREAM-SNAPSHOT-MVP
  - WI-LRH-SERVE-SAFE-DEFAULT-MVP
  - WI-EXECUTION-READINESS-SCHEMA
  - WI-RUN-PACKET-DRY-RUN
  - WI-RUN-REPORT-MVP
  - WI-AGENT-BRANCH-CONTAINMENT
  - WI-GITHUB-PR-CI-OBSERVATION
  - WI-BOUNDED-STABILIZATION-LOOP-DESIGN
  - WI-WORK-ITEM-EXECUTION-READY-CONCEPT-MVP
  - WI-RUN-PACKET-GENERATION-DESIGN-MVP
exit_criteria:
  - execution-framework design is updated and reconciled with the workstream/planning-tree model
  - roadmap, current focus, and work items identify the first execution-framework implementation phase
  - first implementation work items are scoped before runtime automation begins
  - first implementation package starts with shared state APIs, planning relationship validation, snapshot-visible planning summaries, a safe-default serve skeleton, execution readiness, dry-run run packets, and run reports
  - execution readiness and run-packet contracts are defined before agent backends are added
  - human/policy gates for merge, release, publish, and closeout remain explicit
---

# Safe-Default Execution Framework

## Purpose

This workstream represents the next major stream of LRH project-control work after the Workstream
Control Plane MVP: designing and staging a safe-default execution framework for approved executable leaves. The effort
should turn the proposed execution-framework architecture into reviewable roadmap, focus, and
work-item plans before any runtime automation begins.

The core idea is that default LRH should first help humans inspect current state, generate and edit
prompts, record manual evidence, and prepare durable run artifacts. Optional agentic capability may
later automate stereotyped PR/review/CI stabilization loops for selected work items while preserving
bounded authority, least privilege, auditable evidence, and human/policy gates for merge, release,
publish, and closeout.

The canonical living design is `project/design/execution_framework_mvp.md`. It defines the current
layered structure: core state APIs; safe-default `lrh serve` viewer/prompt workbench; durable run
packets, run state, awaited transitions, and reports; read-only observation adapters; optional
agentic execution adapters; and later daemon/dashboard modes.

The intended future execution shape is:

```text
selected executable leaf
-> shared planning relationship/index model
-> planning relationship validation
-> snapshot-visible planning summary
-> local `lrh serve` viewer / prompt workbench
-> explicit human action
-> run packet and durable run state
-> manual evidence and report
-> later read-only observation
-> optional agentic branch/PR/stabilization adapters only when explicitly enabled
```

## Rationale

LRH now has a first-class control-plane vocabulary for workstreams, planning-tree relationships, and
work items as executable leaves. The execution-framework proposal captures the next architectural
boundary: how LRH might eventually help execute selected leaves without granting unbounded autonomy
or bypassing repository review.

Representing that effort as a workstream keeps the transition explicit. This workstream should
reconcile the proposed execution layers with the adopted planning-tree model, identify the first safe
implementation phase, and preserve the safe-default boundary that keeps autonomous execution,
branch mutation, PR creation, CI-fix loops, review-fix loops, merge, and publish outside core LRH
until contracts, policy gates, evidence expectations, and optional packaging are clear.

## Relevant context

Canonical living design/context package:

- `project/design/execution_framework_mvp.md` — current MVP architecture and staged plan for bounded execution.

- Adopted planning-tree proposal:
  `project/design/proposals/adopted/workstreams-and-recursive-planning-tree/00_proposal.md`
- Proposed execution-framework proposal:
  `project/design/proposals/proposed/workstream-execution-framework/00_proposal.md`
- Execution-framework layer documents:
  `project/design/proposals/proposed/workstream-execution-framework/`
- Workstream schema MVP:
  `project/design/workstream_schema_mvp.md`
- Current focus context:
  `project/focus/current_focus.md`
- Execution, evidence, and status roadmap context:
  `project/roadmap/phase_03_execution_evidence_status.md`
- Planning-tree and workstream foundation background:
  `project/roadmap/phase_01a_planning_tree_workstreams.md`
- Existing execution-readiness/run-packet planning seeds:
  `WI-WORK-ITEM-EXECUTION-READY-CONCEPT-MVP` and `WI-RUN-PACKET-GENERATION-DESIGN-MVP`

## Exit criteria

This workstream can move toward resolution when:

- execution-framework design is updated and reconciled with the workstream/planning-tree model;
- roadmap, current focus, and work items identify the first execution-framework implementation phase;
- first implementation work items are scoped before runtime automation begins;
- first implementation package starts with shared state APIs, planning relationship validation, snapshot-visible planning summaries, a safe-default serve skeleton, execution readiness, dry-run run packets, and run reports;
- execution readiness and run-packet contracts are defined before agent backends are added; and
- human/policy gates for merge, release, publish, and closeout remain explicit.

## Non-goals

This workstream does not immediately implement:

- agent runtime execution;
- autonomous agent dispatch;
- branch mutation in default LRH;
- automatic PR creation;
- automated CI-fix or review-response loops;
- automatic merge to main;
- release or publish automation;
- GitHub token or permission automation;
- MCP bridges;
- telemetry systems;
- full `lrh run` automation;
- making `lrh serve` an autonomous runner; or
- backend-specific Codex, Claude, or native adapters.

This project-control artifact also does not add CLI behavior, validation behavior, execution
backends, orchestration loops, tests for runtime execution behavior, or GitHub API integration.

## Next phase

Generate a prompt package for the first implementation sequence:

- `WI-LRH-CORE-STATE-APIS-MVP`
- `WI-LRH-SERVE-SAFE-DEFAULT-MVP`
- `WI-EXECUTION-READINESS-SCHEMA`
- `WI-RUN-PACKET-DRY-RUN`
- `WI-RUN-REPORT-MVP`

Do not start branch mutation, backend adapters, autonomous execution, PR creation, or PR
stabilization automation before those contracts exist.
