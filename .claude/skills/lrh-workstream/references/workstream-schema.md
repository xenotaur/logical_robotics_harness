# LRH Workstream — YAML Frontmatter Field Reference

This document is the field reference for LRH workstream YAML frontmatter.
Validated against `src/lrh/control/validator.py` (`WORKSTREAM_REQUIRED_FIELDS`,
`WORKSTREAM_KINDS`, `WORKSTREAM_STATUS`, `WORKSTREAM_STAGE`,
`WORKSTREAM_LIST_FIELDS`). See `project/workstreams/README.md` for lifecycle
semantics and the authoritative schema description.

---

## Required fields (`WORKSTREAM_REQUIRED_FIELDS`)

These fields are checked by `lrh validate` and must be present on every
workstream.

| Field | Type | Constraints |
|---|---|---|
| `id` | string | Stable, unique identifier; LRH projects conventionally use `WS-*` form. Not schema-enforced — follow the project's established convention. |
| `kind` | string | Must be exactly `planning_node` (the only valid value in `WORKSTREAM_KINDS`) |
| `title` | string | Short human-readable title; used in listings and snapshots |
| `status` | string | See status vocabulary below |
| `stage` | string | See stage vocabulary below |

### Status → directory bucket (`WORKSTREAM_STATUS`, `WORKSTREAM_BUCKETS`)

| `status` | Directory |
|---|---|
| `proposed` | `project/workstreams/proposed/` |
| `active` | `project/workstreams/active/` |
| `resolved` | `project/workstreams/resolved/` |
| `abandoned` | `project/workstreams/abandoned/` |

`lrh validate` reports a warning (not error) for bucket/status mismatches.
Use `lrh workstreams organize --apply` to move files to their correct buckets.

---

## Stage vocabulary (`WORKSTREAM_STAGE`)

`stage` gives the fine-grained process position within the current `status`.

| Value | Meaning |
|---|---|
| `conceived` | Idea captured but not yet formally assessed |
| `assessed` | Pros/cons reviewed; direction chosen |
| `designed` | Design reviewed; approach locked |
| `planned` | Roadmap, focus, and work items defined |
| `executing` | Work items actively being implemented |
| `reviewing` | Implementation done; under review/validation |
| `closed` | Work complete and accepted |
| `abandoned` | Intentionally stopped, rejected, or superseded |

`lrh validate` checks the value against this vocabulary and emits an error
for unrecognised values. Use `conceived` as the default for a newly created
workstream unless a more advanced stage is already established.

---

## List fields (`WORKSTREAM_LIST_FIELDS`)

These fields must be lists when present — `lrh validate` errors if they are
not.

| Field | Type | Notes |
|---|---|---|
| `children` | list of strings | `WS-*` IDs of child planning nodes |
| `related_focus` | list of strings | `FOCUS-*` IDs from `project/focus/` |
| `related_roadmap` | list of strings | `ROADMAP-*` IDs from `project/roadmap/` |
| `related_design` | list of strings | File paths to related design docs and proposals |
| `work_items` | list of strings | `WI-*` IDs of work items belonging to this workstream |
| `execution_records` | list of strings | Execution record IDs linked to this workstream |
| `evidence` | list of strings | `EV-*` IDs or paths to evidence artifacts |
| `exit_criteria` | list of strings | Conditions that must be true before closure |

---

## Conventional fields

Not validated by the schema but present on most well-formed workstreams.

| Field | Type | Notes |
|---|---|---|
| `summary` | string | One-sentence description; shown in `lrh snapshot project` output |
| `origin` | string | How the workstream came to exist: `ad_hoc`, `follow_up`, `design_review`, etc. |
| `parent_id` | string or null | `WS-*` ID of the parent planning node (for sub-workstreams) |
| `rationale` | string | Brief narrative explaining why this workstream exists |
| `closeout` | string | Notes on how the workstream was resolved |

---

## Minimum valid frontmatter

```yaml
---
id: WS-EXAMPLE
kind: planning_node
title: Short descriptive title
status: proposed
stage: conceived
---
```

## Recommended new-workstream frontmatter

```yaml
---
id: WS-EXAMPLE
kind: planning_node
title: Short descriptive title
status: proposed
stage: conceived
origin: ad_hoc
summary: One-sentence description of what this workstream coordinates.
related_focus: []
related_roadmap: []
related_design: []
work_items: []
exit_criteria: []
---
```

## Full example (from an existing workstream)

```yaml
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
  - WI-LRH-SERVE-SAFE-DEFAULT-MVP
exit_criteria:
  - execution-framework design is updated and reconciled with the workstream/planning-tree model
  - first implementation work items are scoped before runtime automation begins
---
```
