---
id: FOCUS-WORKSTREAM-CONTROL-PLANE-MVP
title: Establish planning-tree semantics and workstreams safely
status: active
priority: high
owner: anthony
related_principles:
  - PRINCIPLES-ENGINEERING
  - PRINCIPLES-EVALUATION
related_roadmap:
  - ROADMAP-PHASE-01A
---

# Current Focus

The immediate priority is establishing **planning-tree semantics and workstreams** as core LRH
control-plane concepts. This remains a safe-default, non-agentic planning effort: LRH should be able
to model, validate, and summarize planning relationships while humans remain responsible for deciding
and executing work.

Recently completed:

- reconciled near-term workstream design around recursive planning-tree concepts
- accepted workstreams as user-facing planning nodes and work items as execution-ready leaves
- aligned planning-tree work with safe-default packaging, where agentic execution is optional and deferred
- retained workstream execution framework layers as deferred long-term architecture
- closed prior release/toolchain and proposal alignment work needed before this planning step

## Why this is active now

LRH needs a disciplined next sequence that introduces workstreams as first-class planning artifacts
without jumping to runtime execution, orchestration, or autonomous behavior. This preserves
repository-as-control-plane and manual-mode parity while keeping implementation slices small and
reviewable.

## Safe-default requirements

All planning-tree and workstream work must:

1. function without agentic capabilities or optional `lrh[agentic]` dependencies
2. support human-assisted workflows by default, including reviewable prompts or run packets
3. prepare future agentic execution by preserving explicit planning metadata and readiness concepts
4. avoid autonomous invocation of coding agents, execution loops, PR stabilization loops, or adapters
5. mark any agentic run command, adapter, stabilization-loop, or sandbox-envelope work as deferred / future / requires `lrh[agentic]`

Command naming convention: use `lrh agentic run` or `lrh-agentic run` for future autonomous execution.
Treat older `lrh run` references as deferred execution-framework shorthand unless a future command-design
work item explicitly assigns safe-default or installed-agentic alias semantics.

## Priorities

1. Define planning-node schema and recursive relationship conventions (`parent_id`, `children`).
2. Define execution-ready work items as human-executable leaves, not autonomous runs.
3. Define planning-tree validation rules for references, cycles, and consistency before implementation.
4. Define and document minimal workstream artifact conventions and bucket navigation.
5. Define workstream-to-work-item relationship conventions compatible with the planning-tree model.
6. Add design-level snapshot visibility and human-assisted run-packet generation work items.
7. Only after design-level slices are clear, implement loader/model, validation, snapshot, and dry-run-first organize/tidy support through small reviewed work items.

## Non-Goals

- Implementing runtime features, schemas in code, validation logic, or CLI commands in the planning PR.
- Implementing `lrh agentic run` or any autonomous run command.
- Adding agent runtime execution, orchestration, adapters, or automated stage advancement.
- Adding PR stabilization loops or sandbox-envelope behavior.
- Implementing MCP bridges, telemetry systems, or backend adapters.
- Collapsing multiple MVP slices into one large implementation change.

## Exit Criteria

This focus is complete when:

1. roadmap and work items clearly sequence the Planning Tree and Workstream Foundation
2. workstreams are represented in project control as first-class artifacts
3. planning-node and workstream relationship semantics are documented and validated through small reviewed work items
4. human-assisted workflow generation is specified without implying autonomous execution
5. deferred agentic work remains explicitly out of scope and tied to future optional `lrh[agentic]` capability
6. the next implementation prompt can start with the first concrete MVP work item: `WI-PLANNING-NODE-SCHEMA-MVP`
