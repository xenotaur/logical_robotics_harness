# `lrh dependency-map`

`lrh dependency-map` prints the read-only `DependencyMapSnapshot` of a
dependency-map view. The snapshot is the typed, versioned projection that
every LRH Console map view renders from. It never edits control files.

## `snapshot`

```bash
lrh dependency-map snapshot <view> [--project-root PROJECT_ROOT]
```

Reads `project/views/dependency_maps/<view>.md` and the project's work items
and workstreams, then prints the snapshot as JSON on stdout.

| Exit | Meaning |
|---|---|
| `0` | Printed the snapshot. Problems in the data, such as cycles or missing references, are listed in its `diagnostics`; they are not failures. |
| `1` | The view does not exist, its declaration is invalid, or the control files cannot be loaded. The reason goes to stderr. |
| `2` | No subcommand was given. |

`--project-root` may be the repository root or its `project/` directory.

`lrh serve` serves the same JSON at
`GET /api/project/<project_id>/dependency-maps/<view>`.

## View declarations

A view lives at `project/views/dependency_maps/<view>.md`. Its id must match
the file name. It names canonical IDs only: it never copies work items or
dependency edges.

```yaml
---
id: "example"
title: "Example"
lanes:
- workstream: "WS-EXAMPLE"      # lanes are canonical workstreams
  title: "Example"              # optional
phases:
- id: "foundation"              # ordered organizational rows, not gates
  title: "Foundation"
  work_items: ["WI-ONE", "WI-TWO"]
lane_overrides:                 # optional; chooses a lane, with a reason
- work_item: "WI-THREE"
  lane: "WS-EXAMPLE"
  reason: "Listed in two workstreams; tracked here."
---
```

- An item is in a lane when that workstream lists it in `work_items` or is its
  `parent_id`.
- The view contains every item in its lanes and every item its phases list.
- `lrh validate` reports malformed declarations as
  `DEPENDENCY_MAP_VIEW_INVALID` and unknown IDs as
  `DEPENDENCY_MAP_VIEW_UNKNOWN_REFERENCE`.

## Snapshot contents

- `schema_version` (currently `1`), `view_id`, `view_title`, `view_source`.
  `DependencyMapSnapshot.from_dict` checks every field's type and allowed
  values, and raises `ValueError` for anything that does not fit.
- `project`: the repository directory name, an opaque `checkout_id`, and the
  Git `head` if available. No absolute path is exported.
- `source_fingerprint`: a hash of the control files' paths and contents, so
  uncommitted edits change it. `generated_at` is UTC.
- `lanes` and `phases` in view order. An `unplaced` phase row is always last,
  and an `unplaced` lane row appears when some item has no lane.
- `nodes`, one for each item in the view, plus one for each item outside the
  view that an in-view item references (`offscreen: true`), with:
  - `lifecycle`: the item's own `status`.
  - `state` and `state_reasons`: the structural state, in this precedence:
    `done`; then `blocked` (the item's `blocked` flag, or a `blocked_by`
    target that is not done); then `in_progress`; then `waiting` (a
    `depends_on` prerequisite is not done); then `unblocked` (with reason
    `no_prerequisites` when there are none). An abandoned item has state
    `abandoned`. An item whose `status` is not `proposed`, `active`,
    `resolved`, or `abandoned` has state `unknown` and an `invalid_lifecycle`
    diagnostic; it is never shown as eligible. An abandoned or missing
    prerequisite never counts as done.
  - `prompt_ready`: from `lrh work-items readiness`.
  - `authorization`: always `not_derived`, because LRH grants no per-item
    execution authority.
  - `lane`, `phase`, and their `*_source` provenance: `workstream`,
    `override`, `declared`, `ambiguous`, `none`, or `offscreen`.
  - `offscreen_predecessors`: how many distinct items outside the view it
    references through `depends_on` or `blocked_by`. Those items are included
    with `offscreen: true`, so they are never silently dropped.
- `edges`: each `depends_on` and `blocked_by` reference, with the declaring
  file, and `resolved: false` when the target does not exist.
- `diagnostics`, each with a `code`, `severity`, `message`, and `subjects`:
  `missing_reference`; `cycle`, reported separately per edge type for any
  cycle that touches a shown item; `ambiguous_lane`; `unplaced_lane`;
  `ambiguous_phase`; `unplaced_phase`; `unknown_view_reference`;
  `unused_lane_override`; `invalid_lifecycle`; and `partial_source`. A
  consumer can call `lrh.dependency_maps.snapshot.freshness_diagnostics` to
  get `stale_snapshot` when the sources changed after generation.

There is no effort, duration, or critical-path data, and none is inferred.
