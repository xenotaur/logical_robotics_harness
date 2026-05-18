# Safe-default agentic extra packaging proposal set

This proposal set defines the adopted safe-default package boundary where
normal `lrh` installs remain non-agentic and autonomous capability is
explicit opt-in via future `lrh[agentic]` and/or `lrh-agentic` behavior.

## Status

`adopted` / `partial`

The safe-default packaging/governance decision is folded into canonical
project design documents and current package metadata has no agentic extra.
The implementation remains partial because the optional `lrh[agentic]`
extra, separate `lrh-agentic` distribution, and integrated `lrh agentic`
missing-package dispatcher remain deferred.

## Documents

1. [`00_proposal.md`](00_proposal.md)
   — umbrella proposal covering motivation, install semantics,
   capability boundaries, CLI behavior, migration strategy, phased
   implementation, validation expectations, tradeoffs, and
   recommendation posture.

## Reading order

1. `README.md` (this file)
2. `00_proposal.md`

## Canonical-document touchpoints

The adopted decision is reflected in:

- `project/design/design.md`
- `project/design/architecture.md`
- `project/design/repository_spec.md`
- `docs/how-to/run-a-release.md`
