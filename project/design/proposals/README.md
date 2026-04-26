# Design Proposals

This directory holds longer-form design proposals that go beyond the
existing `project/design/design.md`, `project/design/architecture.md`,
and `project/design/repository_spec.md`. Proposals are grouped into
proposal sets (one subdirectory each) so that a single coherent body
of work — a top-level umbrella plus its sub-proposals and worked-
example appendices — can be reviewed together.

## What lives here

A proposal set is a directory under `project/design/proposals/`
containing one or more design documents that share an `id:` prefix
and a single umbrella document. Each document carries
`type: design_proposal` in its YAML frontmatter and either a
`parent:` link (for sub-proposals and appendices) or no parent
(for the umbrella document at the top of the set).

Proposals are working artifacts. They become canonical only when
their decisions are folded into `design.md`, `architecture.md`,
`repository_spec.md`, or one of the related authoritative documents
under `project/design/`, and the proposal's `status:` is set to
`accepted` or `superseded`.

## Lifecycle

`status: proposed` — drafted but not yet adopted. The author or a
reviewer may still substantively change the proposal.

`status: accepted` — the design has been adopted. Subsequent
changes go through new proposals or directly through edits to the
canonical documents (with the proposal updated to reflect them).

`status: superseded` — replaced by a later proposal; reference the
replacement in the frontmatter `superseded_by:` field.

`status: rejected` — considered and explicitly declined. Kept for
history.

## Current proposal sets

[`workstream-execution-framework/`](workstream-execution-framework/)
— Proposes adding a typed `workstream` artifact between focus and
work_items, with a six-layer execution stack (control plane →
templates → orchestration → agent runtime → observability+evidence
→ MCP bridges). Status: `proposed`. Includes a Pass-B worked-example
appendix (`WS-LCATS-CORPORA-ANALYSIS`).

## Proposal-set conventions

A proposal set directory name should be a stable, descriptive slug
(`workstream-execution-framework/`, not `proposal-001/`).

The umbrella document is `00_proposal.md`. Sub-proposals are
numbered `01_*.md`, `02_*.md`, ... in reading order. Appendices
use the prefix `appendix_` (e.g., `appendix_b_lcats_corpora_\
analysis.md`).

Each proposal-set directory contains its own `README.md` with a
reading order, status summary, and links into the canonical
documents the proposal touches. See `workstream-execution-\
framework/README.md` for the worked example.

Proposals follow `STYLE.md` (Markdown line-wrapping, frozen
dataclasses in code samples, module-not-member imports, UTF-8) and
`AGENTS.md` (evidence-grounded reasoning, manual-mode parity where
applicable, repository-as-control-plane).

## Cross-references

Proposals must reference rather than duplicate canonical documents.
When a proposal would update `design.md` or `architecture.md`, it
states the diff in narrative form; the actual document edits land
when the proposal is accepted, in a follow-on changeset that flips
`status:` to `accepted`.
