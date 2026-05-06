# Workstream Schema MVP

This document defines the documentation-level MVP schema for LRH workstream artifacts.
It records the field vocabulary and semantics that future loader, validation, snapshot, and
planning-tree indexing work should use as its starting point.

This is an MVP schema. It may evolve through later focused work items, but changes should preserve
human readability and the separation between source Markdown under `project/` and typed runtime
objects under `src/lrh/`.

## Scope

This schema applies to Markdown workstream artifacts under `project/workstreams/`. It is a
project-control convention only; it does not implement runtime loaders, validation logic, CLI
behavior, execution backends, agent orchestration, or `lrh run`.

## User-facing and internal model

The user-facing vocabulary remains intentionally small:

```text
Project -> Workstream -> Work Item
```

The internal planning model is tree-ready:

```text
Project = root planning context
Workstream = planning node
Work Item = executable leaf
```

Users should normally reason in terms of Project, Workstream, and Work Item rather than abstract
planning nodes.

## Metadata authority

Workstream YAML frontmatter is authoritative for identity, lifecycle state, process stage, and
planning relationships. Directory placement under `project/workstreams/` is a human-facing
navigation projection.

The `status` field is intended to align with the bucket directory:

```text
project/workstreams/proposed/
project/workstreams/active/
project/workstreams/resolved/
project/workstreams/abandoned/
```

Future validators may report drift when metadata and directory placement disagree. Future organize
or tidy commands may reconcile that drift based on metadata. This mirrors the existing work-item
policy that metadata is the source of truth and bucket placement is derived.

## Minimal frontmatter shape

A minimal proposed workstream can be represented as:

```yaml
---
id: WS-EXAMPLE
kind: planning_node
title: Example Workstream
status: proposed
stage: conceived
origin: ad_hoc
summary: Small illustrative example workstream.
---
```

## Required fields

The MVP required fields are:

- `id`: stable, unique workstream identifier. Prefer a `WS-` prefix for workstream IDs.
- `kind`: artifact kind. The initial workstream kind is `planning_node`.
- `title`: short human-readable title.
- `status`: coarse lifecycle state and intended bucket name.
- `stage`: finer-grained process position within the lifecycle.

## Optional fields

The MVP optional field vocabulary is:

- `origin`: where the workstream came from, such as `ad_hoc`, a roadmap item, a design proposal, or
  a work item.
- `parent_id`: metadata reference to the parent planning context or parent workstream.
- `children`: metadata references to child planning artifacts.
- `summary`: concise summary for scans and snapshots.
- `rationale`: why the workstream exists or why this grouping is useful.
- `related_focus`: related current-focus IDs.
- `related_roadmap`: related roadmap IDs.
- `work_items`: related work-item IDs when callers need an explicit work-item list separate from
  general `children` relationships.
- `execution_records`: related prompt execution records or execution-record IDs/paths.
- `evidence`: related evidence IDs or paths.
- `exit_criteria`: conditions that should be satisfied before the workstream is resolved.
- `closeout`: resolution summary, terminal rationale, or links to closeout notes.

Optional fields should stay lightweight. They document references and intent; they do not imply
automated execution, automatic stage advancement, or runtime enforcement in this PR.

## Kind vocabulary

The initial kind vocabulary for workstreams is intentionally narrow:

```text
planning_node
```

Do not introduce workstream subtypes until a later schema or validation change demonstrates the
need. Work items remain separately modeled executable leaves.

## Status semantics

`status` is the coarse lifecycle bucket for a workstream.

Initial status vocabulary:

```text
proposed
active
resolved
abandoned
```

Semantics:

- `proposed`: being considered, assessed, or designed.
- `active`: currently being executed or reviewed.
- `resolved`: completed and closed out.
- `abandoned`: intentionally stopped, rejected, superseded, or otherwise not continuing.

Status should match bucket placement for human navigation, but metadata remains authoritative.
Future validation may flag mismatches and future organize/tidy behavior may repair them.

## Stage semantics

`stage` is the finer-grained process position of a workstream.

Initial stage vocabulary:

```text
conceived
assessed
designed
planned
executing
reviewing
closed
abandoned
```

Semantics:

- `conceived`: identified as a possible workstream.
- `assessed`: reviewed enough to decide whether it is worth designing or planning.
- `designed`: design direction exists, but implementation sequencing may not be ready.
- `planned`: roadmap, focus, or work-item sequencing is clear enough to proceed.
- `executing`: child work items or related project-control updates are in progress.
- `reviewing`: outputs are being evaluated, reconciled, or prepared for closeout.
- `closed`: completed and closed out.
- `abandoned`: intentionally stopped, rejected, or superseded.

Status is coarse lifecycle state; stage is finer process position. Future validation may constrain
allowed status/stage combinations, but this document does not make those combinations hard runtime
rules.

## Parent and child relationship semantics

Planning-tree relationships are metadata-driven. They should not rely on nested folders or path
placement as the source of truth.

Use:

```yaml
parent_id: WS-PARENT
children:
  - WS-CHILD
  - WI-CHILD-WORK-ITEM
```

Relationship guidance:

- `parent_id` identifies the immediate parent planning context when one is known.
- `children` lists known child planning artifacts that this workstream owns or coordinates.
- Workstream-to-workstream and workstream-to-work-item relationships should be expressible through
  metadata.
- Project-root planning contexts may eventually be represented explicitly, but this MVP does not
  require a new root artifact.
- Future validation/indexing may check reference existence, uniqueness, cycle safety, and
  consistency between parent and child declarations.

For ordinary use, contributors should still describe and review relationships as Project,
Workstream, and Work Item relationships. The planning-tree language is an internal-ready
model, not a new user-facing directory taxonomy.

## Non-goals

This schema MVP does not implement:

- runtime loaders or typed models
- validation rules or parser behavior
- CLI behavior
- snapshot integration
- organize/tidy behavior
- planning-tree indexing
- `lrh run`
- automation, execution backends, or agent runtime orchestration
- telemetry or MCP systems

Those capabilities should land through later focused Workstream Control Plane MVP work items.
