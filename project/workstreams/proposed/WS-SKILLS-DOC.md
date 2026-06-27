---
id: WS-SKILLS-DOC
kind: planning_node
title: Diataxis Documentation Skills
status: proposed
stage: designed
origin: follow_up
summary: >
  Implement and land three Claude Code documentation workflow skills
  (/lrh-doc-audit, /lrh-doc-organize, /lrh-doc-work) following the
  Option C-1 design established in PROP-LRH-DOC-SKILLS.
related_design:
  - project/design/proposals/proposed/lrh-doc-skills/00_proposal.md
work_items:
  - WI-SKILLS-LRH-DOC-AUDIT
  - WI-SKILLS-LRH-DOC-ORGANIZE
  - WI-SKILLS-LRH-DOC-WORK
exit_criteria:
  - all three skills exist at .claude/skills/ and pass lrh validate with 0 errors
  - all three skills have distributable package copies at src/lrh/skills/
  - CLAUDE.md ## Skills index updated for all three skills
  - each skill has a corresponding resolved work item in project/work_items/resolved/
  - lrh setup installs all three skills to ~/.claude/skills/
---

## Purpose

This workstream groups the design, implementation, and validation of
three LRH documentation workflow skills: `/lrh-doc-audit`,
`/lrh-doc-organize`, and `/lrh-doc-work`. It follows directly from the
`WS-SKILLS` workstream (resolved 2026-06-25), which established the
core skill infrastructure, and is governed by `PROP-LRH-DOC-SKILLS`
(merged 2026-06-27), which locked the Option C-1 approach: skill
references are inspired by the existing `lrh request` templates
(`audit_docs.md`, `organize_docs.md`) but remain separate artifacts,
with drift made explicit through cross-reference comments.

## Background / Rationale

LRH has `lrh request` templates for documentation work (`audit_docs.md`,
`organize_docs.md`) that encode Diataxis practice but target a two-hop
agent architecture (template → populate → send to Codex/CI). Claude Code
collapses that to one hop, making the templates' agent-routing scaffolding
irrelevant in a skill context. A gap also exists: no template covers
post-landing documentation updates. The three skills address both the
adaptation of existing templates and this new use case.

## Scope

- Implement `/lrh-doc-audit`: discover a repository's doc layout, classify
  by Diataxis quadrant, produce a structured audit artifact at
  `project/audits/docs/docs-audit-YYYY-MM-DD.md`
- Implement `/lrh-doc-organize`: implement one scoped reorganization phase
  from an audit artifact (or from a discovery pass), opening a reviewable PR
- Implement `/lrh-doc-work`: update docs to reflect recently completed work
  (merged PR, resolved work item, or closed workstream)
- Deliver distributable package copies at `src/lrh/skills/<name>/` for
  global installation via `lrh setup`
- Add cross-reference comments to the existing `audit_docs.md` and
  `organize_docs.md` templates

## Work Items

- **`WI-SKILLS-LRH-DOC-AUDIT`** — Implement the `/lrh-doc-audit` skill:
  `SKILL.md`, `references/diataxis-criteria.md`,
  `references/audit-requirements.md`, `src/lrh/skills/lrh-doc-audit/`
  package copy, `CLAUDE.md` index entry, cross-reference comment in
  `audit_docs.md`.
- **`WI-SKILLS-LRH-DOC-ORGANIZE`** — Implement the `/lrh-doc-organize`
  skill: `SKILL.md`, `references/diataxis-criteria.md`,
  `references/organize-constraints.md`, `references/organize-workflow.md`,
  `src/lrh/skills/lrh-doc-organize/` package copy, `CLAUDE.md` index entry,
  cross-reference comment in `organize_docs.md`.
- **`WI-SKILLS-LRH-DOC-WORK`** — Implement the `/lrh-doc-work` skill:
  `SKILL.md`, `references/diataxis-criteria.md`,
  `references/doc-work-scope.md`, `src/lrh/skills/lrh-doc-work/` package
  copy, `CLAUDE.md` index entry. Scope may be refined after the first two
  skills are dogfooded.

## Exit Criteria

- All three skills exist at `.claude/skills/` and pass `lrh validate`
  with 0 errors and 0 warnings
- All three skills have distributable package copies at `src/lrh/skills/`
- `CLAUDE.md ## Skills` index updated for all three skills
- Each skill has a corresponding resolved work item in
  `project/work_items/resolved/`
- `lrh setup` installs all three skills to `~/.claude/skills/`

## Non-Goals

- Does not apply the Diataxis audit to LRH's own existing documentation —
  that is a separate effort, a natural use of `/lrh-doc-audit` once it exists
- Does not implement `lrh doc` as a CLI subgroup — skills are the interface
- Does not upload skills to the claude.ai Skills API — out of scope per
  `PROP-LRH-DOC-SKILLS`
- Does not migrate prior `lrh request audit_docs` or `lrh request
  organize_docs` run artifacts
