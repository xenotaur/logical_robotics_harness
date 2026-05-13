---
id: ROADMAP-PHASE-03
title: Execution, Evidence, and Status
status: proposed
parent: ROADMAP-CORE
order: 3
success_criteria:
  - planning relationship/index validation and snapshot summaries are shared before serve/run surfaces infer planning-tree state
  - safe-default `lrh serve` can project current control-plane state without autonomous behavior
  - execution readiness fields are defined for selected executable leaves
  - dry-run run packets can be prepared without branch mutation or agent invocation
  - final run reports can summarize status, validation evidence, human verification tasks, and next actions
  - branch-contained PR stabilization remains bounded by explicit human/policy gates
  - run artifacts are organized predictably
---

# Phase 3 — Execution, Evidence, and Status

This phase gives LRH operational value by preparing bounded, auditable execution workflows for
selected executable leaves. The immediate phase is not to make agents autonomous. It is to define
and validate execution readiness and run-packet contracts before mutation-capable automation,
agent backends, or PR stabilization loops are implemented.

Canonical living design: `project/design/execution_framework_mvp.md`. Its staged structure now starts
with shared core state APIs, a planning relationship/index model, relationship validation,
snapshot-visible planning summaries, and a safe-default `lrh serve` viewer/prompt workbench, then
durable run artifacts, read-only observation adapters, optional agentic execution adapters, and later
daemon or dashboard modes.

## Goal

LRH can prepare and eventually run bounded, auditable execution workflows for selected executable
leaves. The default path first helps humans inspect state, generate prompts, record evidence, and
manage run artifacts; optional agentic layers may later add branch-contained PR stabilization while
preserving human/policy gates.

## Staged deliverables

1. Shared core state and interpretation APIs.
2. Shared planning relationship/index model and validation.
3. Snapshot-visible planning summaries.
4. Safe-default `lrh serve` read-only viewer and prompt workbench.
5. Opt-in execution readiness schema.
6. Run packet request/dry-run distinction.
7. Durable run state and manual run tracking.
8. Run report MVP.
9. Agent branch containment design support.
10. GitHub PR/CI observation adapter.
11. Bounded stabilization loop design.
12. Backend adapter abstraction.
13. Manual/assisted/bounded-auto mode progression.

## First implementation package

The first implementation package should stay contract-first and dry-run-first:

- `WI-LRH-CORE-STATE-APIS-MVP`
- `WI-WORKSTREAM-PLANNING-TREE-RELATIONSHIPS-MVP` / `WI-PLANNING-TREE-VALIDATION-RULES-MVP`
- `WI-WORKSTREAM-SNAPSHOT-MVP`
- `WI-LRH-SERVE-SAFE-DEFAULT-MVP`
- `WI-EXECUTION-READINESS-SCHEMA`
- `WI-RUN-PACKET-DRY-RUN`
- `WI-RUN-REPORT-MVP`

These work items should establish shared CLI/server planning interpretation, the minimum local assist
surface, project-control fields, packet contents, report contents, validation evidence expectations,
and human closeout tasks needed before any branch mutation or backend adapter work begins.

## Explicit deferrals

This phase does not start with full automation. Defer the following until later phases or optional
capability work has stable contracts and policy gates:

- automatic merge to main
- release or publish automation
- secrets management beyond documented policy assumptions
- privileged workflow execution
- MCP bridges
- telemetry systems
- full autonomous execution
- default-layer agent dispatch, branch mutation, automatic PR creation, CI-fix loops, review-fix loops, merge, or publish
- backend-specific implementations until contracts are stable
- autonomous branch mutation before readiness, packet, and report contracts exist

## Risks

- status prose becoming detached from validation evidence
- too much automation before readiness, packet, and report contracts exist
- branch mutation escaping path, review, or policy boundaries
- backend-specific behavior hardening before LRH has stable neutral contracts
