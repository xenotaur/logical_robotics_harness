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
→ MCP bridges). Status: `proposed` (deferred long-term execution architecture).
Near-term design decisions are captured in the accepted
`workstreams-and-recursive-planning-tree/` proposal set; this set
remains a retained source for long-term runtime/orchestration design
concepts and should be revisited after workstream artifacts, validation,
snapshots, and roadmap/focus/work-item alignment are in place. Includes
a Pass-B worked-example appendix (`WS-LCATS-CORPORA-ANALYSIS`).


[`workstreams-and-recursive-planning-tree/`](workstreams-and-recursive-planning-tree/)
— Proposes a documentation-first, minimal workstream planning model
(Project → Workstream → Work Item) with recursive planning-tree
semantics kept internal-ready and explicit non-goals deferring runtime
implementation. Status: `accepted` (near-term design basis). The documentation-level
Workstream Schema MVP is captured in `project/design/workstream_schema_mvp.md`.


[`safe-default-agentic-extra-packaging/`](safe-default-agentic-extra-packaging/)
— Proposes safe-default non-agentic `lrh` installs with explicit
opt-in autonomous capability via `lrh[agentic]` and/or `lrh-agentic`.
Status: `proposed` (packaging/governance boundary design; implementation deferred).

[`tag-push-pypi-publishing/`](tag-push-pypi-publishing/)
— Proposes Option D tag-push release design for publishing the
safe-default `lrh` distribution to PyPI via Trusted Publishing
(OIDC), with TestPyPI rehearsal, installed-wheel smoke checks, and
evidence-backed release outputs. Status: `accepted` (canonical release
direction; implementation deferred).

[`prompt-execution-search-and-match/`](prompt-execution-search-and-match/)
— Proposes shared execution-record parsing and query infrastructure for
exact prompt-ID lookup, prompt-file-to-record matching, and exploratory
execution-record search. Status: `implemented` command surface, retained as
background design context for the package-owned lookup, match, and search
workflow documented in `PROMPTS.md` and `project/executions/README.md`.

[`design-proposal-lifecycle-traceability/`](design-proposal-lifecycle-traceability/)
— Proposes first-class design-proposal decision lifecycle metadata,
separate implementation lifecycle metadata, and traceability to work
items and evidence. Status: `proposed` (design-only; implementation
deferred).

## Machine-readable proposal metadata

LRH validates Markdown files under this tree as design-proposal artifacts when
their YAML frontmatter declares either `type: design_proposal` or the
compatibility alias `kind: design_proposal`. `type: design_proposal` is the
canonical spelling for new documents. If both `type` and `kind` are present,
they must agree.

Proposal IDs may use the current LRH `PROP-...` form or downstream `DP-...`
forms. Lifecycle-aware proposal frontmatter supports:

```yaml
id: PROP-EXAMPLE
type: design_proposal
status: proposed | adopted | accepted | rejected | superseded
implementation_status: not_started | partial | implemented | deferred | obsolete
implemented_by:
  - WI-...
evidence:
  - EV-...
supersedes:
  - PROP-...
superseded_by: PROP-...
```

`adopted` is the preferred status for a governing design decision. `accepted`
is still accepted as a legacy spelling and is treated as equivalent to
`adopted` for validation and bucket checks. Implementation claims should be
traceable through `implemented_by` work-item IDs and/or `evidence` IDs.

Frontmatter `status` is authoritative. Lifecycle bucket directories
(`proposed/`, `adopted/`, `rejected/`, and `superseded/`) are derived
human-readable organization aids. Unbucketed proposal files and bucket/status
mismatches are reported as warnings by `lrh validate`.

Use the organizer to preview or apply lifecycle bucket moves without modifying
proposal contents:

```bash
lrh design organize
lrh design organize --apply
```

The organizer preserves filenames, treats legacy `accepted` as equivalent to the
`adopted/` bucket, skips README/index and non-proposal Markdown files, and
refuses unsafe overwrites.

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
