---
id: ROADMAP-PHASE-03
title: Execution, Evidence, and Status
status: proposed
parent: ROADMAP-CORE
order: 3
success_criteria:
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

Canonical living design: `project/design/execution_framework_mvp.md`. Its staged structure is Phase 1: `lrh run` structural support, Phase 2: ecosystem observation and containment adapters, and Phase 3: bounded runtime execution.

## Goal

LRH can prepare and eventually run bounded, auditable execution workflows for selected executable
leaves, using run packets, branch-contained PR stabilization, validation evidence, and final run
reports while preserving human/policy gates.

## Staged deliverables

1. Execution readiness schema.
2. Run packet dry-run.
3. Run report MVP.
4. Agent branch containment design support.
5. GitHub PR/CI observation adapter.
6. Bounded stabilization loop design.
7. Backend adapter abstraction.
8. Manual/assisted/bounded-auto mode progression.

## First implementation package

The first implementation package should stay contract-first and dry-run-first:

- `WI-EXECUTION-READINESS-SCHEMA`
- `WI-RUN-PACKET-DRY-RUN`
- `WI-RUN-REPORT-MVP`

These work items should establish the minimum project-control fields, packet contents, report
contents, validation evidence expectations, and human closeout tasks needed before any branch
mutation or backend adapter work begins.

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
- backend-specific implementations until contracts are stable
- autonomous branch mutation before readiness, packet, and report contracts exist

## Risks

- status prose becoming detached from validation evidence
- too much automation before readiness, packet, and report contracts exist
- branch mutation escaping path, review, or policy boundaries
- backend-specific behavior hardening before LRH has stable neutral contracts
