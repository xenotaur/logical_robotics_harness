# Workstreams

Workstreams are first-class LRH project-control artifacts for meaningful streams of work.
They are user-facing planning records that group design, planning, work items, prompt execution,
review, evidence, and closeout over time.

Use workstreams when an effort is substantial enough that its context, decisions, sequencing, and
closeout should remain visible in `project/`. Trivial fixes and obvious maintenance tasks do not
require heavyweight workstream ceremony.

## User-facing model

The normal vocabulary is intentionally simple:

```text
Project -> Workstream -> Work Item
```

Users should not need to reason about abstract planning nodes during ordinary use. The internal,
future-compatible model is:

```text
Project = root planning context
Workstream = planning node
Work Item = executable leaf
```

This lets LRH keep a human-readable repository model now while remaining compatible with future
planning-tree validation and summarization.

The documentation-level schema for workstream frontmatter is defined in
[`project/design/workstream_schema_mvp.md`](../design/workstream_schema_mvp.md).

## Status buckets

Workstreams are grouped under lifecycle buckets for human navigation:

```text
proposed/   workstreams being considered or designed
active/     workstreams currently being executed or reviewed
resolved/   workstreams completed and closed out
abandoned/  workstreams intentionally stopped, rejected, or superseded
```

A future workstream may be represented as a single Markdown file or a directory with a manifest and
supporting notes. In either case, bucket placement is a navigational projection, not the ultimate
source of truth.

## Minimal frontmatter fields

The MVP required workstream frontmatter fields are:

- `id`
- `kind`
- `title`
- `status`
- `stage`

The initial workstream `kind` is `planning_node`. Optional fields include `origin`, `parent_id`,
`children`, `summary`, `rationale`, `related_focus`, `related_roadmap`, `work_items`,
`execution_records`, `evidence`, `exit_criteria`, and `closeout`. See the schema MVP document for
field semantics and non-goals.

## Metadata is authoritative

Workstream frontmatter is the source of truth for workstream identity and lifecycle state. In
particular, the frontmatter `status` value is authoritative; directory bucket placement exists so
humans can scan the repository quickly.

Future validators may report drift when a workstream's metadata and directory placement disagree.
Future organize or tidy commands may repair that drift based on metadata, following the same
metadata-authoritative pattern used for work items.

## Status versus stage

The initial MVP vocabulary distinguishes coarse lifecycle from finer process position:

```text
status = coarse lifecycle / bucket
stage  = fine-grained process position
```

Initial status vocabulary:

```text
proposed | active | resolved | abandoned
```

Initial stage vocabulary:

```text
conceived | assessed | designed | planned | executing | reviewing | closed | abandoned
```

These terms capture the accepted near-term design direction, but this directory README does not make
them runtime validation rules by itself. Schema, loader, validator, snapshot, and organizer behavior
will land in later focused work items.

## Large-work lifecycle

For substantial, architectural, high-risk, or cross-cutting work, LRH should avoid jumping directly
from an idea to a prompt package. The preferred lifecycle is:

```text
idea -> assessment / pros-and-cons review -> workstream initiation
workstream -> design review -> update project/design
project design -> plan review -> update roadmap, current focus, and work items
focus review -> work item selection -> prompt package
prompt execution -> execution record -> evidence -> status / closeout
```

Each major transition should leave the `project/` control plane more accurate than before. This is a
lifecycle principle for meaningful work, not a requirement that every small edit create a workstream.

## Relationship to work items and execution records

Workstreams aggregate and contextualize meaningful efforts. They can describe why an effort exists,
what design or planning decisions shaped it, how work items relate to each other, and what closeout
should prove.

Work items remain the concrete executable units. They should stay narrowly scoped and independently
reviewable, even when they belong to a larger workstream.

Prompt IDs and execution records record what happened during prompt-driven work. Evidence remains
the basis for completion claims. A workstream may link to related work items, prompt execution
records, evidence, decisions, design updates, roadmap changes, or focus updates, but it does not
replace those artifacts.

## Non-goals for this directory MVP

This directory establishes the human-facing home and introductory documentation for workstreams. It
does not yet provide:

- schema validation
- loaders or runtime models
- snapshot integration
- organizer or tidy behavior
- `lrh run`
- agent execution
- orchestration
- MCP bridges
- telemetry systems
- execution backends or adapters

Those capabilities should be implemented later through separate, focused Workstream Control Plane
MVP work items.
