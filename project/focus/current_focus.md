---
id: FOCUS-WORKSTREAM-CONTROL-PLANE-MVP
title: Plan and sequence the Workstream Control Plane MVP
status: active
priority: high
owner: anthony
related_principles:
  - PRINCIPLES-ENGINEERING
  - PRINCIPLES-EVALUATION
---

# Current Focus

The immediate priority is the **Workstream Control Plane MVP**: establish manual,
project-control-first workstream representation before any execution automation.

Recently completed:

- reconciled near-term workstream design around recursive planning-tree concepts
- retained workstream execution framework as deferred long-term architecture
- closed prior release/toolchain and proposal alignment work needed before this planning step

## Why this is active now

LRH needs a disciplined next sequence that introduces workstreams as first-class planning artifacts
without jumping to runtime execution or orchestration. This preserves repository-as-control-plane and
manual-mode parity while keeping implementation slices small and reviewable.

## Priorities

1. Define and document minimal workstream artifact conventions and bucket navigation.
2. Add typed loader/model support for workstreams as planning nodes.
3. Validate workstream metadata, status/stage semantics, IDs, and bucket/status drift.
4. Add planning-tree relationship checks that stay metadata-driven.
5. Add workstream snapshot and, only after validation is stable, dry-run-first organize/tidy support.

## Non-Goals

- Implementing `lrh run`.
- Adding agent runtime execution, orchestration, or automated stage advancement.
- Implementing MCP bridges, telemetry systems, or backend adapters.
- Collapsing multiple MVP slices into one large implementation change.

## Exit Criteria

This focus is complete when:

1. roadmap and work items clearly sequence the Workstream Control Plane MVP
2. workstreams are represented in project control as first-class artifacts
3. validation and snapshot coverage for workstreams are implemented through small reviewed work items
4. deferred execution-framework layers remain explicitly out of scope
5. the next prompt package can start with the first concrete MVP work item (directory/README or schema)
