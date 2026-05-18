# Workstreams and Recursive Planning Tree Proposal Set

This proposal set defines a documentation-first design for introducing
first-class workstreams as LRH planning artifacts while keeping runtime
implementation explicitly out of scope for this change.

## Status

`adopted` / `partial`

## Documents

1. [`00_proposal.md`](00_proposal.md)
   — umbrella proposal covering purpose, motivation, user-visible
   artifacts, minimal schema, status/stage semantics, recursive tree
   relationships, validation expectations, snapshot expectations,
   non-goals, and recommended sequencing.

## Scope notes

This proposal set is adopted as the near-term design basis. Implementation
is partial: workstream documentation, schema, loader/model, validation,
and planning-tree relationship slices have corresponding work items;
autonomous runtime execution remains deferred.

## Reading order

1. `README.md` (this file)
2. `00_proposal.md`

## Canonical-document touchpoints (on acceptance)

This proposal is adopted as the near-term basis for
workstream modeling. Follow-on project-control updates should align
roadmap, current focus, and work items before implementation prompts are
generated. Canonical design/control touchpoints include:

- `project/design/design.md`
- `project/design/architecture.md`
- `project/design/repository_spec.md`

