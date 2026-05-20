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

Proposals are working artifacts. Lifecycle-aware proposals distinguish
`status`, which answers whether the design decision governs the project,
from `implementation_status`, which answers whether the governed design
has been delivered. Implementation claims should be backed by
`implemented_by` work items and `evidence` links.

Adopted design proposals govern future work even before implementation
lands. Their decisions may later be folded into `design.md`,
`architecture.md`, `repository_spec.md`, or one of the related
authoritative documents under `project/design/`.

## Lifecycle

Design proposals use two separate lifecycle axes: `status` answers
whether the design decision governs the project, while
`implementation_status` answers whether the governed design has been
delivered and should be backed by `implemented_by` and/or `evidence`.
The adopted design direction is captured in
[`adopted/design-proposal-lifecycle-traceability/00_proposal.md`](adopted/design-proposal-lifecycle-traceability/00_proposal.md).

`status: proposed` — drafted but not yet adopted. The author or a
reviewer may still substantively change the proposal.

`status: adopted` — the design has been adopted. Subsequent
changes go through new proposals or directly through edits to the
canonical documents (with the proposal updated to reflect them).

`status: superseded` — replaced by a later proposal; reference the
replacement in the frontmatter `superseded_by:` field.

`status: rejected` — considered and explicitly declined. Kept for
history.

Implementation is staged separately from proposal adoption. The
lifecycle-traceability proposal defines this order: parser and
validation model; `lrh design organize`; snapshot reporting; and
dogfood migration across LRH's own proposal set.

## Current proposal sets


[`proposed/activity-lanes-and-observational-dashboard.md`](proposed/activity-lanes-and-observational-dashboard.md)
— Proposes a lightweight, tool-agnostic activity-lane model (`project/activity/ACT-*.md`) plus
observational adapters and derived dashboard snapshots so LRH can coordinate mixed workflows
(ChatGPT, Codex Cloud/App, Claude, VS Code/manual editing, GitHub PR stabilization) without
requiring centralized `lrh run` mediation. Status: `proposed` / `not_started` (documentation-only
proposal; no runtime implementation in this PR).

[`proposed/lrh-conversations-storage-interop/`](proposed/lrh-conversations-storage-interop/)
— Proposes a unified architecture for LRH Conversations, policy-aware storage,
and external agent interop so raw AI-assisted development conversations remain
private-by-default, non-authoritative until promoted, scoped, auditable, and
portable across tools. The set now includes a focused ChatGPT PDF conversion
adapter design as an early manual capture path from browser Save as PDF exports
to private-by-default, non-authoritative Markdown transcripts. Status: `proposed`
/ `not_started` (documentation-only direction; no storage, chat UI, converter,
scanner, MCP, GitHub, HTTP, model-provider, or run execution implementation).

[`proposed/lrh-console-visual-language/`](proposed/lrh-console-visual-language/)
— Proposes Alternative D, the Enhanced Swimlane Console, as the future light/dark visual language
for `lrh serve` dashboards and LRH Console views, with UX review criteria and a first implemented
`lrh serve` checklist for evaluating safe-default tranches without making mockups pixel-perfect
acceptance criteria. Status: `proposed` / `not_started` (documentation-only direction; no UI, CSS,
server-route, frontend-framework, or safe-default MVP scope changes).

[`proposed/lrh-serve-operational-triage-mvp/`](proposed/lrh-serve-operational-triage-mvp/)
— Proposes a safe-default, read-only/meta-aware `lrh serve` operational triage dashboard and
prompt workbench for registered projects, deterministic swimlanes, project/design/workstream/work-item
drill-down, readiness-aware prompt affordances, and first-class capability gaps. Status: `proposed` /
`not_started` (documentation-only direction; no UI, server-route, write endpoint, autonomous dispatch,
or repository-mutation behavior).

[`proposed/workstream-execution-framework/`](proposed/workstream-execution-framework/)
— Proposes future bounded execution for already-approved executable
leaves: run packet → agent-owned branch → pull request → bounded
CI/review stabilization → final run report → human/policy merge and
closeout gate. Status: `proposed` (now staged through the `WS-EXECUTION-FRAMEWORK`
planning workstream, starting with readiness, dry-run packet, and report contracts before
automation). The updated umbrella is the current entry point; older layer documents remain retained
background for runtime, lifecycle, evidence, observability, and bridge concepts. Includes a Pass-B
worked-example appendix (`WS-LCATS-CORPORA-ANALYSIS`).


[`proposed/ci-capability-scaffolding.md`](proposed/ci-capability-scaffolding.md)
— Proposes reusable CI capability scaffolding through a human playbook, CI request-template refresh,
later CI Agent Skill prototype design, and dogfooded template/fragments reassessment. Status:
`proposed` / `not_started` (design/control-plane alignment only; no CI workflow, playbook, template,
or skill implementation in the proposal PR).

[`proposed/constitutional-sandbox-envelope/`](proposed/constitutional-sandbox-envelope/)
— Proposes a constitutional sandbox envelope for future autonomous and
semi-autonomous LRH execution: agents may propose arbitrary actions, but
only policy-checked, sandboxed, logged, and interruptible capabilities may
execute. Status: `proposed` / `not_started` (documentation-only design;
no runtime behavior changes).

[`adopted/workstreams-and-recursive-planning-tree/`](adopted/workstreams-and-recursive-planning-tree/)
— Proposes a documentation-first, minimal workstream planning model
(Project → Workstream → Work Item) with recursive planning-tree
semantics kept internal-ready and explicit non-goals deferring runtime
implementation. Status: `adopted` / `partial` (near-term design basis
with control-plane slices underway). The documentation-level Workstream
Schema MVP is captured in `project/design/workstream_schema_mvp.md`.


[`adopted/safe-default-agentic-extra-packaging/`](adopted/safe-default-agentic-extra-packaging/)
— Proposes safe-default non-agentic `lrh` installs with explicit
opt-in autonomous capability via `lrh[agentic]` and/or `lrh-agentic`.
Status: `adopted` / `partial` (canonical packaging/governance boundary;
optional agentic extra/package behavior remains deferred).

[`adopted/tag-push-pypi-publishing/`](adopted/tag-push-pypi-publishing/)
— Proposes Option D tag-push release design for publishing the
safe-default `lrh` distribution to PyPI via Trusted Publishing
(OIDC), with TestPyPI rehearsal, installed-wheel smoke checks, and
evidence-backed release outputs. Status: `adopted` / `partial`
(canonical release direction; release-tag CI is implemented, while PyPI
publishing remains deferred).

[`adopted/prompt-execution-search-and-match/`](adopted/prompt-execution-search-and-match/)
— Proposes shared execution-record parsing and query infrastructure for
exact prompt-ID lookup, prompt-file-to-record matching, and exploratory
execution-record search. Status: `adopted` / `implemented` command surface,
retained as background design context for the package-owned lookup, match,
and search workflow documented in `PROMPTS.md` and
`project/executions/README.md`.

[`adopted/design-proposal-lifecycle-traceability/`](adopted/design-proposal-lifecycle-traceability/)
— Proposes first-class design-proposal decision lifecycle metadata,
separate implementation lifecycle metadata, and traceability to work
items and evidence. Status: `adopted` / `partial` (parser/model,
validation, organization, and snapshot slices are implemented; broader
lifecycle dogfooding remains ongoing).

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
`lrh snapshot project` reports a compact design-proposal lifecycle summary,
grouping adopted proposals by implementation status, showing superseded
replacements, and displaying concise work-item/evidence traceability for
partial or implemented designs.

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

The organizer preserves filenames and proposal-set relative paths under the
derived lifecycle bucket, treats legacy `accepted` as equivalent to the
`adopted/` bucket, skips README/index and non-proposal Markdown files, and
refuses unsafe overwrites. Plain `index.md` files are ignored by both validation
and organization.

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
states the diff in narrative form. Canonical document edits may land in
the same changeset that adopts the proposal, or later when
implementation work begins. The proposal `status:` remains the
authoritative decision lifecycle signal.
