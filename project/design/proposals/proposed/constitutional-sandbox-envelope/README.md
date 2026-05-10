# Constitutional sandbox envelope proposal set

This proposal set defines a proposed LRH security-by-design subsystem for
future autonomous and semi-autonomous execution. It describes a capability-
limited, policy-checked, sandboxed, auditable envelope for agent actions.

## Status

`proposed` / `not_started`

This is a documentation-only design proposal. It does not implement the
envelope, grant agents new authority, add MCP integrations, or change the
current validation/runtime behavior.

## Documents

1. [`00_proposal.md`](00_proposal.md)
   — umbrella proposal covering motivation, threat framing, layered
   architecture, capability policy, sandbox runtime options, evidence,
   e-stop behavior, constitutional review, phased implementation,
   tradeoffs, non-goals, and open questions.

## Reading order

1. `README.md` (this file)
2. `00_proposal.md`

## Canonical-document touchpoints

If adopted later, this proposal would likely inform future updates to:

- `project/design/design.md`
- `project/design/architecture.md`
- `project/design/repository_spec.md`
- future `lrh run` and agent-adapter documentation
