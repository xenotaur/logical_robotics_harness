---
id: WS-EXECUTION-FRAMEWORK
kind: planning_node
title: Bounded Agent Execution Framework
status: proposed
stage: conceived
origin: follow_up
summary: Define and plan LRH's bounded execution loop for executable leaves, including run packets, agent-owned branches, PR/CI stabilization, and final run reports.
related_focus:
  - FOCUS-WORKSTREAM-CONTROL-PLANE-MVP
related_roadmap:
  - ROADMAP-PHASE-01A
  - ROADMAP-PHASE-02
work_items:
  - WI-WORK-ITEM-EXECUTION-READY-CONCEPT-MVP
  - WI-RUN-PACKET-GENERATION-DESIGN-MVP
exit_criteria:
  - execution-framework design is updated and reconciled with the workstream/planning-tree model
  - roadmap, current focus, and work items identify the first execution-framework implementation phase
  - first implementation work items are scoped before runtime automation begins
  - execution readiness and run-packet contracts are defined before agent backends are added
  - human/policy gates for merge, release, publish, and closeout remain explicit
---

# Bounded Agent Execution Framework

## Purpose

This workstream represents the next major stream of LRH project-control work after the Workstream
Control Plane MVP: designing and staging a bounded execution loop for approved executable leaves.
The effort should turn the proposed execution-framework architecture into reviewable roadmap, focus,
and work-item plans before any runtime automation begins.

The core idea is that LRH should automate stereotyped PR/review/CI stabilization loops for selected
work items while preserving bounded authority, least privilege, auditable evidence, and human/policy
gates for merge, release, publish, and closeout.

The intended future execution shape is:

```text
selected executable leaf
-> run packet
-> agent-owned branch
-> pull request
-> bounded review/CI stabilization loop
-> final run report
-> human/policy merge and closeout gate
```

## Rationale

LRH now has a first-class control-plane vocabulary for workstreams, planning-tree relationships, and
work items as executable leaves. The execution-framework proposal captures the next architectural
boundary: how LRH might eventually help execute selected leaves without granting unbounded autonomy
or bypassing repository review.

Representing that effort as a workstream keeps the transition explicit. This workstream should
reconcile the proposed execution layers with the adopted planning-tree model, identify the first safe
implementation phase, and preserve the safe-default boundary that keeps autonomous execution outside
core LRH until contracts, policy gates, and evidence expectations are clear.

## Relevant context

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
- Planning-tree and workstream foundation roadmap:
  `project/roadmap/phase_01a_planning_tree_workstreams.md`
- Runtime and workspace roadmap context:
  `project/roadmap/phase_02_runtime_and_workspace.md`
- Existing execution-readiness/run-packet planning seeds:
  `WI-WORK-ITEM-EXECUTION-READY-CONCEPT-MVP` and `WI-RUN-PACKET-GENERATION-DESIGN-MVP`

## Exit criteria

This workstream can move toward resolution when:

- execution-framework design is updated and reconciled with the workstream/planning-tree model;
- roadmap, current focus, and work items identify the first execution-framework implementation phase;
- first implementation work items are scoped before runtime automation begins;
- execution readiness and run-packet contracts are defined before agent backends are added; and
- human/policy gates for merge, release, publish, and closeout remain explicit.

## Non-goals

This workstream does not immediately implement:

- agent runtime execution;
- automatic merge to main;
- release or publish automation;
- GitHub token or permission automation;
- MCP bridges;
- telemetry systems;
- full `lrh run` automation; or
- backend-specific Codex, Claude, or native adapters.

This project-control artifact also does not add CLI behavior, validation behavior, execution
backends, orchestration loops, tests for runtime execution behavior, or GitHub API integration.

## Next phase

Update roadmap, current focus, and work items to plan the execution-framework phase.
