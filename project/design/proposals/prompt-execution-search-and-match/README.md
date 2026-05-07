# Prompt Execution Search and Match Proposal

Status: `proposed`

Reading order:

1. [`00_proposal.md`](00_proposal.md) — proposes shared execution-record
   parsing and query infrastructure for exact prompt-ID lookup,
   prompt-file-to-record matching, and exploratory execution-record
   search.

This proposal was written as design-only. The implemented command surface now
preserves `lrh prompt check-execution` as the authoritative exact-match
primitive for prompt soft idempotence and layers `lrh match executions` and
`lrh search executions` on package-owned modules with the same evidence
hierarchy: exact lookup is authoritative, prompt-file matching delegates exact
lookup, and search remains exploratory.

## Canonical-document touchpoints

If accepted and implemented, this proposal is expected to touch these
canonical or near-canonical workflow documents:

- [`PROMPTS.md`](../../../../PROMPTS.md) — prompt ID workflow, soft
  idempotence guidance, and installed prompt command examples.
- [`project/executions/README.md`](../../../executions/README.md) —
  execution-record schema, status lifecycle, and lookup/search guidance.
- [`project/design/design.md`](../../design.md) and
  [`project/design/architecture.md`](../../architecture.md) — only if the
  shared prompt-workflow query modules become part of the accepted core
  architecture narrative.
