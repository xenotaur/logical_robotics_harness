---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-LRH-DOC-AUDIT
title: Implement lrh-doc-audit Claude Code skill
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-SKILLS-DOC
related_design:
  - project/design/proposals/proposed/lrh-doc-skills/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - reorganize_docs
  - implement_lrh_doc_organize
  - implement_lrh_doc_work
acceptance:
  - .claude/skills/lrh-doc-audit/SKILL.md exists with valid frontmatter
  - .claude/skills/lrh-doc-audit/ is an exact copy of src/lrh/skills/lrh-doc-audit/
  - src/lrh/assist/templates/request/audit_docs.md carries a cross-reference comment
  - CLAUDE.md ## Skills has a /lrh-doc-audit entry
  - lrh validate passes with 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - .claude/skills/lrh-doc-audit/SKILL.md
  - .claude/skills/lrh-doc-audit/references/diataxis-criteria.md
  - .claude/skills/lrh-doc-audit/references/audit-requirements.md
  - src/lrh/skills/lrh-doc-audit/SKILL.md
  - src/lrh/skills/lrh-doc-audit/references/diataxis-criteria.md
  - src/lrh/skills/lrh-doc-audit/references/audit-requirements.md
---

## Summary

Implement the `/lrh-doc-audit` Claude Code skill, which audits a repository's
documentation layout, classifies each doc by Diataxis quadrant (tutorial,
how-to, reference, explanation), identifies gaps and stale links, and writes a
structured audit artifact at `project/audits/docs/docs-audit-YYYY-MM-DD.md`.
The skill follows Option C-1 from `PROP-LRH-DOC-SKILLS`: its `references/`
files are inspired by but independent from `audit_docs.md`; a cross-reference
comment links the two.

## Problem / Context

LRH's `lrh request audit_docs` template encodes good Diataxis practice but
targets a two-hop agent architecture. Claude Code is simultaneously prompt
consumer and implementer, making the template's routing scaffolding irrelevant.
This work item produces a first-class skill that Claude Code can invoke
directly, with domain knowledge (Diataxis criteria, audit requirements,
guardrails) encoded in `references/` files readable without parsing the
template format.

## Scope

- `SKILL.md`: 10-step execution flow — parse input, load references, discovery
  pass, Diataxis classification, gap/stale-link identification, draft artifact,
  confirm gate, write `project/audits/docs/docs-audit-YYYY-MM-DD.md`,
  `lrh validate`, offer commit to main
- `references/diataxis-criteria.md`: four-quadrant definitions and
  classification heuristics, inspired by `audit_docs.md` requirements item 6
- `references/audit-requirements.md`: discovery checklist, audit artifact
  schema (required sections including "Proposed first PR scope"), guardrails
  (no doc reorganization in this operation), inspired by `audit_docs.md`
  requirements 1–5 and 7–11
- `src/lrh/skills/lrh-doc-audit/`: exact package copy for `lrh setup`
- Cross-reference comment added to `src/lrh/assist/templates/request/audit_docs.md`
- `CLAUDE.md ## Skills` index entry

## Required Changes

1. Create `src/lrh/skills/lrh-doc-audit/SKILL.md`
2. Create `src/lrh/skills/lrh-doc-audit/references/diataxis-criteria.md`
3. Create `src/lrh/skills/lrh-doc-audit/references/audit-requirements.md`
4. Copy `src/lrh/skills/lrh-doc-audit/` to `.claude/skills/lrh-doc-audit/` (byte-for-byte)
5. Add cross-reference comment to `src/lrh/assist/templates/request/audit_docs.md`
6. Add `/lrh-doc-audit` entry to `CLAUDE.md ## Skills`
7. Verify `diff -r src/lrh/skills/lrh-doc-audit/ .claude/skills/lrh-doc-audit/` is empty

## Non-Goals

- Does not perform a doc audit of any repository — implements the skill only
- Does not modify `organize_docs.md` (belongs to WI-SKILLS-LRH-DOC-ORGANIZE)
- Does not implement `/lrh-doc-organize` or `/lrh-doc-work`
- Does not upload the skill to the claude.ai Skills API

## Acceptance Criteria

- `.claude/skills/lrh-doc-audit/SKILL.md` exists with valid frontmatter
  (`name`, `description`, `disable-model-invocation: true`, `argument-hint`)
- `.claude/skills/lrh-doc-audit/` is an exact copy of `src/lrh/skills/lrh-doc-audit/`
- `src/lrh/assist/templates/request/audit_docs.md` carries the comment:
  `<!-- Skill reference: .claude/skills/lrh-doc-audit/references/ -->`
- `CLAUDE.md ## Skills` has a `/lrh-doc-audit` entry
- `lrh validate` passes with 0 errors

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `diff -r src/lrh/skills/lrh-doc-audit/ .claude/skills/lrh-doc-audit/`
