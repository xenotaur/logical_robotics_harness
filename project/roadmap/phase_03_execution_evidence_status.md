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

Canonical living design: `project/design/execution_framework_mvp.md`. Its staged structure separates
prerequisite control-plane alignment from the first execution-contract package. Shared core state
APIs, planning relationship/index validation, and snapshot-visible planning summaries must be
available before packet generation relies on them. The first package is execution readiness, dry-run
run packets, and run reports; safe-default `lrh serve`, durable run state UI, read-only observation
adapters, optional agentic execution adapters, and later daemon/dashboard modes follow separately.

## Goal

LRH can prepare and eventually run bounded, auditable execution workflows for selected executable
leaves. The default path first helps humans inspect state, generate prompts, record evidence, and
manage run artifacts; optional agentic layers may later add branch-contained PR stabilization while
preserving human/policy gates.

## Staged deliverables

The deliverable list is grouped by package boundary. It is not a single prompt package, and the
read-only `lrh serve` workbench is intentionally deferred until after the first execution-contract
package.

### Prerequisite control-plane alignment

1. Shared core state and interpretation APIs.
2. Shared planning relationship/index model and validation.
3. Snapshot-visible planning summaries.

### First execution-contract package

1. Opt-in execution readiness schema.
2. Run packet request/dry-run distinction.
3. Run report MVP.

### Deferred follow-on packages

1. Safe-default `lrh serve` read-only viewer and prompt workbench.
2. Durable run state and manual run tracking.
3. Agent branch containment design support.
4. GitHub PR/CI observation adapter.
5. Bounded stabilization loop design.
6. Backend adapter abstraction.
7. Manual/assisted/bounded-auto mode progression.

### Adjacent reusable capability work

The CI capability scaffolding proposal (`project/design/proposals/ci-capability-scaffolding.md`)
and workstream (`project/workstreams/proposed/WS-CI-CAPABILITY-SCAFFOLDING.md`) are adjacent to
Phase 3 evidence and stabilization planning. They keep CI setup, assessment, implementation,
debugging, and
hardening guidance staged as a playbook and prompt/skill follow-up rather than a one-size-fits-all
workflow template.

## First execution-contract implementation package

The first execution-framework implementation package should stay contract-first and dry-run-first:

1. `WI-EXECUTION-READINESS-SCHEMA`
2. `WI-RUN-PACKET-DRY-RUN`
3. `WI-RUN-REPORT-MVP`

These work items establish project-control fields, packet contents, report contents, validation
evidence expectations, and human closeout tasks needed before any branch mutation or backend adapter
work begins.

Prerequisites for that package are shared state/API interpretation, planning relationship/index
validation, and snapshot-visible planning summaries. They should be verified before the first package
starts and completed in a separate prerequisite prompt if missing. `WI-LRH-SERVE-SAFE-DEFAULT-MVP` is
a later read-only/local-assist package, not part of the first execution-contract package.

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
