# Prompt Execution Search and Match Proposal

Status: `proposed`

Reading order:

1. [`00_proposal.md`](00_proposal.md) — proposes shared execution-record
   parsing and query infrastructure for exact prompt-ID lookup,
   prompt-file-to-record matching, and exploratory execution-record
   search.

This proposal is design-only. It preserves `lrh prompt check-execution`
as the authoritative exact-match primitive for prompt soft idempotence
and recommends layering future `lrh match executions` and
`lrh search executions` commands on shared package-owned modules.
