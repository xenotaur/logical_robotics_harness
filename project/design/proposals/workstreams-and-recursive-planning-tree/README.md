# Workstreams and Recursive Planning Tree Proposal Set

This proposal set defines a documentation-first design for introducing
first-class workstreams as LRH planning artifacts while keeping runtime
implementation explicitly out of scope for this change.

## Status

`proposed`

## Documents

1. [`00_proposal.md`](00_proposal.md)
   — umbrella proposal covering purpose, motivation, user-visible
   artifacts, minimal schema, status/stage semantics, recursive tree
   relationships, validation expectations, snapshot expectations,
   non-goals, and recommended sequencing.

## Scope notes

This proposal-set PR records design intent only. It does not add parser
or model code, validators, CLI commands, runtime execution behavior,
workstream directory creation, or automation.

## Reading order

1. `README.md` (this file)
2. `00_proposal.md`

## Canonical-document touchpoints (on acceptance)

When accepted, this proposal is expected to drive follow-on updates to
canonical design/control documents rather than becoming canonical by
itself. Anticipated touchpoints:

- `project/design/design.md`
- `project/design/architecture.md`
- `project/design/repository_spec.md`

