# LRH Serve operational triage MVP proposal set

This proposal set records the proposed safe-default operational triage
surface for `lrh serve`: a read-only/meta-aware dashboard and prompt
workbench for deciding and launching human-gated prompt-driven work.

## Status

`proposed` / `not_started`

This is a documentation-only design proposal. It does not implement UI,
CSS, server routes, frontend dependencies, autonomous dispatch,
repository mutation, execution-record writes, or prompt-saving behavior.

## Documents

1. [`00_proposal.md`](00_proposal.md)
   — umbrella proposal covering product purpose, authority boundaries,
   high-level architecture, information architecture, project cards,
   detail views, prompt workbench behavior, capability gaps,
   accessibility, security/privacy constraints, implementation sequence,
   validation strategy, risks, open questions, and relationships to
   existing LRH design documents.

## Reading order

1. `README.md` (this file)
2. `00_proposal.md`

## Canonical-document touchpoints

If adopted later, this proposal would likely inform future updates to:

- `project/design/execution_framework_mvp.md`
- `project/design/meta_control_plane_mvp_spec.md`
- `project/design/workstream_schema_mvp.md`
- future `lrh serve` route/view-model implementation documentation
