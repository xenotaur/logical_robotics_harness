---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-LRH-DOC-ORGANIZE
title: Implement lrh-doc-organize Claude Code skill
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
  - reorganize_lrh_docs
  - implement_lrh_doc_work
acceptance:
  - .claude/skills/lrh-doc-organize/SKILL.md exists with valid frontmatter
  - .claude/skills/lrh-doc-organize/ is an exact copy of src/lrh/skills/lrh-doc-organize/
  - src/lrh/assist/templates/request/organize_docs.md carries a cross-reference comment
  - CLAUDE.md ## Skills has a /lrh-doc-organize entry
  - lrh validate passes with 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - .claude/skills/lrh-doc-organize/SKILL.md
  - .claude/skills/lrh-doc-organize/references/diataxis-criteria.md
  - .claude/skills/lrh-doc-organize/references/organize-constraints.md
  - .claude/skills/lrh-doc-organize/references/organize-workflow.md
  - src/lrh/skills/lrh-doc-organize/SKILL.md
  - src/lrh/skills/lrh-doc-organize/references/diataxis-criteria.md
  - src/lrh/skills/lrh-doc-organize/references/organize-constraints.md
  - src/lrh/skills/lrh-doc-organize/references/organize-workflow.md
---

## Summary

Implement the `/lrh-doc-organize` Claude Code skill, which implements one
scoped phase of Diataxis-informed documentation reorganization as a reviewable
PR. When a docs-audit artifact is provided it reads the "Proposed first PR
scope" to determine the phase; without one it runs a small discovery pass
before scoping. The skill follows Option C-1 from `PROP-LRH-DOC-SKILLS`.

## Problem / Context

`lrh request organize_docs` generates a downstream prompt for an external
agent. Claude Code can implement the reorganization directly with filesystem
access, branch creation, and PR opening — no intermediate prompt needed. This
work item encodes the organize workflow as a skill with a proper confirm gate,
LRH execution record, and traceability back to the governing proposal.

## Scope

- `SKILL.md`: 10-step execution flow — parse input (audit-path, phase), load
  references, read audit artifact or run discovery pass, scope one phase,
  confirm gate, create branch, implement moves/stubs/README updates, validate,
  commit and open PR, create AD_HOC execution record
- `references/diataxis-criteria.md`: per-skill copy of Diataxis criteria
- `references/organize-constraints.md`: scope source rules (audit vs.
  discovery), path-preservation requirements, README update rules, Diataxis
  boundary rules, planned-vs-implemented distinction — inspired by
  `organize_docs.md` constraints
- `references/organize-workflow.md`: lifecycle context (relationship to
  `/lrh-doc-audit` and `/lrh-doc-work`), execution record convention
- `src/lrh/skills/lrh-doc-organize/`: exact package copy for `lrh setup`
- Cross-reference comment added to `src/lrh/assist/templates/request/organize_docs.md`
- `CLAUDE.md ## Skills` index entry

## Required Changes

1. Create `src/lrh/skills/lrh-doc-organize/SKILL.md`
2. Create `src/lrh/skills/lrh-doc-organize/references/diataxis-criteria.md`
3. Create `src/lrh/skills/lrh-doc-organize/references/organize-constraints.md`
4. Create `src/lrh/skills/lrh-doc-organize/references/organize-workflow.md`
5. Copy `src/lrh/skills/lrh-doc-organize/` to `.claude/skills/lrh-doc-organize/` (byte-for-byte)
6. Add cross-reference comment to `src/lrh/assist/templates/request/organize_docs.md`
7. Add `/lrh-doc-organize` entry to `CLAUDE.md ## Skills`
8. Verify `diff -r src/lrh/skills/lrh-doc-organize/ .claude/skills/lrh-doc-organize/` is empty

## Non-Goals

- Does not reorganize any repository's docs — implements the skill only
- Does not modify `audit_docs.md` (belongs to WI-SKILLS-LRH-DOC-AUDIT)
- Does not implement `/lrh-doc-audit` or `/lrh-doc-work`
- Does not upload the skill to the claude.ai Skills API

## Acceptance Criteria

- `.claude/skills/lrh-doc-organize/SKILL.md` exists with valid frontmatter
- `.claude/skills/lrh-doc-organize/` is an exact copy of `src/lrh/skills/lrh-doc-organize/`
- `src/lrh/assist/templates/request/organize_docs.md` carries the comment:
  `<!-- Skill reference: .claude/skills/lrh-doc-organize/references/ -->`
- `CLAUDE.md ## Skills` has a `/lrh-doc-organize` entry
- `lrh validate` passes with 0 errors

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `diff -r src/lrh/skills/lrh-doc-organize/ .claude/skills/lrh-doc-organize/`
