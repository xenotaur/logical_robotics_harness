# LRH Codex Conversation Exporter proposal set

This proposal set records the proposed Codex app conversation export path for
LRH: private-by-default transcript artifacts with structured manifests,
deterministic inspection commands, and deferred local viewer support.

## Status

`proposed` / `not_started`

This is a documentation-only design proposal. It does not implement a Codex
adapter, transcript archive, manifest schema, inspection command, viewer route,
storage backend, redaction pipeline, or promotion workflow.

## Documents

1. [`00_proposal.md`](00_proposal.md)
   — umbrella proposal covering motivation, prior art, export artifact shape,
   privacy and authority defaults, inspection-before-viewing, optional local
   viewer support, adapter scope, implementation plan, and open questions.
2. [`backlog.md`](backlog.md)
   — proposal-local pointer to the canonical backlog entries for Codex skill
   adaptation issues encountered while creating and landing this proposal.

## Reading order

1. `README.md` (this file)
2. `00_proposal.md`
3. `backlog.md`

## Canonical-document touchpoints

If adopted later, this proposal would likely inform future updates to:

- `docs/conversations/`
- `docs/reference/cli/conversation.md`
- `docs/reference/cli/serve.md`
- `project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md`
- `project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md`
