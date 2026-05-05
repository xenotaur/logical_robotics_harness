# Safe-default agentic extra packaging proposal set

This proposal set defines a design target where default `lrh` installs
remain non-agentic and autonomous capability is explicit opt-in via
`lrh[agentic]` and/or `lrh-agentic`.

## Status

`proposed`

## Documents

1. [`00_proposal.md`](00_proposal.md)
   — umbrella proposal covering motivation, install semantics,
   capability boundaries, CLI behavior, migration strategy, phased
   implementation, validation expectations, tradeoffs, and
   recommendation posture.

## Scope notes

This proposal-set change is design-only. It does not implement package
splits, optional-dependency metadata, module moves, or CLI behavior
changes.

## Reading order

1. `README.md` (this file)
2. `00_proposal.md`

## Canonical-document touchpoints (on acceptance)

If accepted, follow-on canonical updates are expected in:

- `project/design/design.md`
- `project/design/architecture.md`
- `project/design/repository_spec.md`
