# LRH Conversations, Storage, and External Agent Interop proposal set

This proposal set records the proposed unified architecture for LRH
Conversations, Storage, and External Agent Interop.

## Status

`proposed` / `not_started`

This is a documentation-only design proposal. It does not implement storage,
conversation APIs, chat UI, MCP, GitHub integration, HTTP endpoints, model
provider integration, or run execution behavior.

## Documents

1. [`00_proposal.md`](00_proposal.md)
   — umbrella proposal covering motivation, target use cases, core decisions,
   storage and conversation models, adapter surfaces, security and privacy,
   implementation phases, open questions, and tradeoffs.
2. [`01_chatgpt_pdf_import.md`](01_chatgpt_pdf_import.md)
   — focused design note and future command contract for converting ChatGPT
   browser Save as PDF exports into private-by-default, non-authoritative
   Markdown conversation transcripts.

## Reading order

1. `README.md` (this file)
2. `00_proposal.md`
3. `01_chatgpt_pdf_import.md`

## Canonical-document touchpoints

If adopted later, this proposal would likely inform future updates to:

- `project/design/design.md`
- `project/design/architecture.md`
- `project/design/meta_control_plane_mvp_spec.md`
- `project/design/execution_framework_mvp.md`
- future storage, conversation, adapter, and `lrh serve` documentation
