---
id: PROP-LRH-DOC-SKILLS
type: design_proposal
title: LRH Diataxis Documentation Skills — lrh-doc-audit, lrh-doc-organize, lrh-doc-work
status: proposed
created_on: 2026-06-27
updated_on: 2026-06-27
implementation_status: not_started
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md
  - project/workstreams/resolved/WS-SKILLS.md
  - src/lrh/assist/templates/request/audit_docs.md
  - src/lrh/assist/templates/request/organize_docs.md
---

# LRH Diataxis Documentation Skills — `lrh-doc-audit`, `lrh-doc-organize`, `lrh-doc-work`

## Summary

This proposal introduces three Claude Code skills that bring
Diataxis-informed documentation workflows into LRH as first-class slash
commands: `/lrh-doc-audit` (classify a repository's docs against the
Diataxis four-quadrant framework and produce a structured audit artifact),
`/lrh-doc-organize` (implement one scoped phase of the reorganization as a
reviewable PR), and `/lrh-doc-work` (update docs to reflect recently
completed work such as a merged PR, resolved work item, or closed
workstream).

It also adopts **Option C-1** as LRH policy for the relationship between
`lrh request` templates and Claude Code skill references: templates inspire
references but remain separate artifacts; drift between them is accepted
and made visible through cross-reference comments.

## Background and Motivation

LRH has accumulated `lrh request` templates for documentation work —
`audit_docs.md` and `organize_docs.md` — that encode good Diataxis practice
but target a two-hop architecture: template → populate variables → send as
a prompt to a downstream agent (Codex, external CI). Claude Code is
simultaneously the prompt consumer and the implementer, making the two-hop
indirection unnecessary and the templates' agent-routing scaffolding
irrelevant noise.

The `WS-SKILLS` workstream (resolved 2026-06-25) established the core skill
infrastructure — `lrh-create-skill`, `lrh-implement`, `lrh-review-response`
— and proved the pattern. Documentation workflow is the natural next domain.
There is also a gap the templates do not address: keeping docs current as
work lands. No existing template covers post-landing documentation updates.

A design session (2026-06-26) evaluated three structural options for how
skills should relate to the existing templates:

- **Option A** (thin wrappers calling `lrh request`): disqualified because
  the templates are prompt-generators, not execution protocols; routing
  Claude's own generated output back to itself is awkward indirection.
- **Option B** (self-contained skills, logic embedded directly): viable but
  creates two sources of truth with no coupling signal.
- **Option C** (templates inform `references/`, drift accepted): preferred.

Within Option C, the session further resolved:

- **Option C-1** (templates inspire references, accept drift): recommended.
  The templates and skill references serve different consumers at genuinely
  different levels of abstraction. Drift is accepted as correct behavior;
  coupling is made explicit through cross-reference comments in both files.
- **Option C-2** (single source of truth with derivation pipeline): ruled
  out at current scale because the prose-to-prose transformation from policy
  → template scaffolding vs. policy → reference framing requires judgment,
  not mechanical automation. The machinery cost does not amortize across the
  current template library size.

## Design Decisions

### Decision 1: Template–reference coupling (Option C-1)

**Question:** How should Claude Code skill references relate to the existing
`lrh request` templates that cover the same domain?

**Options considered:**
- A: Thin wrappers calling `lrh request`, executing the output inline
- B: Self-contained skills, templates and references independent
- C-1: References inspired by templates, drift accepted, cross-references explicit
- C-2: Single policy source derived into both templates and references via build step

**Chosen: C-1.** The Diataxis framework itself supports this: templates are
how-to guides for the `lrh request` CLI; references are reference/explanation
material for Claude Code skill execution. These are different documentation
modes serving different consumers. Drift is expected and correct; the
cross-reference comment surfaces it for human review rather than hiding it.

The cross-reference convention:
- Each skill reference that was inspired by a template carries a comment:
  `<!-- Template counterpart: src/lrh/assist/templates/request/audit_docs.md -->`
- Each template that has a skill reference counterpart carries:
  `<!-- Skill reference: .claude/skills/lrh-doc-audit/references/ -->`

### Decision 2: Per-skill `diataxis-criteria.md` copies

**Question:** Should the Diataxis classification criteria live in a shared
location or in each skill's `references/` independently?

**Options considered:**
- Shared `.claude/references/diataxis-criteria.md` (reduce duplication)
- Per-skill copies in each skill's `references/` (consistent with LRH pattern)

**Chosen: per-skill copies.** Consistent with the established precedent
(`lrh-implement` and `lrh-review-response` each carry their own
`canonical-validation.md`). The Diataxis four-quadrant framework is stable;
independent copies are safe. No cross-skill read machinery needed.

### Decision 3: Audit artifact location

**Question:** Where should the docs-audit artifact produced by
`/lrh-doc-audit` be written?

**Options considered:**
- `docs/docs-audit.md` — visible in the docs tree, mixes control-plane with content
- `project/docs/docs-audit-YYYY-MM-DD.md` — control plane, dated for history

**Chosen: `project/docs/`**. Audit artifacts are planning documents, not
documentation. Placing them in the control plane is consistent with how
execution records, work items, and proposals are stored. The dated filename
preserves history across multiple audit runs.

### Decision 4: `lrh-doc-audit` does not open a PR

**Question:** Should `lrh-doc-audit` open a PR containing the audit artifact?

**Context:** The `audit_docs.md` template assumed a Codex workflow where
every output is a PR. Claude Code has direct filesystem access.

**Chosen: write file, confirm gate, offer commit to main.** The audit
artifact is an additive new file — no regression risk. A direct commit to
main after the confirm gate is lower friction and appropriate for a planning
document. The skill offers a PR as an alternative if the user prefers.

### Decision 5: `lrh-doc-work` scope resolution

**Question:** What is the unit of "recently completed work" that
`/lrh-doc-work` accepts?

**Chosen: PR URL, WI-ID, or WS-ID; auto-detect from current branch.**
Disambiguated by prefix (`https://` → PR, `WI-` → work item, `WS-` →
workstream). Consistent with how `lrh-review-response` auto-detects its PR.

## Non-Goals

- Does not replace the `lrh request audit_docs` or `lrh request
  organize_docs` templates for non-Claude-Code agent workflows (Codex, CI
  agents). Those templates remain the correct entry point for those contexts.
- Does not introduce a build step or derivation pipeline between templates
  and references (Option C-2 is explicitly deferred).
- Does not add a shared `.claude/references/` directory — all references
  remain per-skill.
- Does not implement `lrh doc` as a new CLI subgroup — the skills are the
  interface.
- Does not automate the closeout of existing `audit_docs` runs — prior
  audit artifacts produced via `lrh request` are not migrated.
- Does not migrate existing skill files from `.claude/skills/` to
  `src/lrh/skills/` — distributable copies are a follow-on concern for
  all three skills.

## Implementation Plan

Implementation is governed by workstream `WS-SKILLS-DOC` and three work
items, one per skill. The skills are independent and can be implemented in
any order, but `lrh-doc-audit` first is recommended because its audit
artifact is consumed by `lrh-doc-organize`.

| Work item | Skill | PRs | Dependencies |
|---|---|---|---|
| `WI-SKILLS-LRH-DOC-AUDIT` | `/lrh-doc-audit` | 1 | None |
| `WI-SKILLS-LRH-DOC-ORGANIZE` | `/lrh-doc-organize` | 1 | Audit artifact optional |
| `WI-SKILLS-LRH-DOC-WORK` | `/lrh-doc-work` | 1 | None |

Each work item produces:
- `.claude/skills/<name>/SKILL.md`
- `.claude/skills/<name>/references/*.md` (2 files per skill)
- Cross-reference comment edits to relevant templates
- `CLAUDE.md` skill index entry

`lrh-doc-work` scope may be refined after `lrh-doc-audit` and
`lrh-doc-organize` are implemented and dogfooded.

## Cross-References

- Governing workstream: `project/workstreams/proposed/WS-SKILLS-DOC.md`
- Prior skills proposal: `project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md`
- Skills workstream (resolved): `project/workstreams/resolved/WS-SKILLS.md`
- Template counterparts: `src/lrh/assist/templates/request/audit_docs.md`,
  `src/lrh/assist/templates/request/organize_docs.md`
- Diataxis framework: https://diataxis.fr/ (Daniele Procida)
