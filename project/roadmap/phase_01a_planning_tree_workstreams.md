---
id: ROADMAP-PHASE-01A
title: Planning Tree and Workstream Foundation (Safe-Default Compatible)
status: proposed
parent: ROADMAP-CORE
order: 1.5
success_criteria:
  - planning-node semantics are documented as core non-agentic LRH control-plane behavior
  - workstreams are documented as first-class planning artifacts
  - recursive parent/child planning relationships have documented validation expectations
  - execution-ready work items are defined as human-executable leaves without autonomous execution
  - future agentic execution remains deferred to optional lrh[agentic] capability
---

# Phase 1A — Planning Tree and Workstream Foundation (Safe-Default Compatible)

This phase translates the accepted planning-tree and workstream design into concrete
project-control state before runtime automation. It keeps planning-tree semantics in core LRH and
keeps autonomous execution outside the default install posture.

## Goals

- Introduce planning-node semantics into core LRH as deterministic, non-agentic control-plane behavior.
- Introduce workstreams as first-class planning artifacts that organize related work items.
- Enable recursive planning relationships through metadata such as `parent_id` and `children`.
- Define execution-ready work items as human-executable planning leaves, not autonomous runs.
- Support human-assisted workflows by default, including reviewable run-packet or prompt generation.
- Defer autonomous agent execution to a future optional capability requiring `lrh[agentic]` or `lrh-agentic`.

## Deliverables

- planning-node schema and relationship conventions
- workstream directory and minimal schema documentation
- workstream-to-work-item relationship conventions
- planning-tree validation rule design covering references, cycles, and consistency
- snapshot visibility design for workstreams
- human-assisted run-packet or execution-prompt generation design
- explicit deferred-agentic backlog notes for run commands, adapters, stabilization loops, and sandbox envelope work

## Safe-default boundary

This phase must function without agentic dependencies or autonomous-loop commands. Any future
agentic behavior is a separate opt-in capability and must be marked as deferred / future / requires
`lrh[agentic]` until the optional agentic package boundary exists.

## Exit condition

LRH has an actionable, reviewable project-control plan for planning-tree semantics and workstreams,
with implementation slices that can proceed without adding runtime execution, schemas in code,
validation logic, CLI commands, or agentic behavior in this planning PR.
