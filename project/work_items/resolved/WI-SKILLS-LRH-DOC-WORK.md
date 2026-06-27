---
resolution: Implemented /lrh-doc-work skill in PR #338 (commit cd12f8c); SKILL.md (12-step flow with prompt-ID mint at Step 3, resolved-only enforcement for WI/WS inputs, gh pr diff in Step 4, generic work-reference placeholder in stub/stale templates), diataxis-criteria.md, doc-work-scope.md created in src/ and mirrored to .claude/; CLAUDE.md updated
blocked_reason: null
blocked: false
id: WI-SKILLS-LRH-DOC-WORK
title: Implement lrh-doc-work Claude Code skill
type: deliverable
status: resolved
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
  - implement_lrh_doc_audit
  - implement_lrh_doc_organize
acceptance:
  - .claude/skills/lrh-doc-work/SKILL.md exists with valid frontmatter
  - .claude/skills/lrh-doc-work/ is an exact copy of src/lrh/skills/lrh-doc-work/
  - CLAUDE.md ## Skills has a /lrh-doc-work entry
  - lrh validate passes with 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - .claude/skills/lrh-doc-work/SKILL.md
  - .claude/skills/lrh-doc-work/references/diataxis-criteria.md
  - .claude/skills/lrh-doc-work/references/doc-work-scope.md
  - src/lrh/skills/lrh-doc-work/SKILL.md
  - src/lrh/skills/lrh-doc-work/references/diataxis-criteria.md
  - src/lrh/skills/lrh-doc-work/references/doc-work-scope.md
---

## Summary

Implement the `/lrh-doc-work` Claude Code skill, which updates a repository's
documentation to reflect recently completed work. The skill accepts a merged PR
URL, a resolved work item ID (`WI-*`), or a closed workstream ID (`WS-*`) —
auto-detecting from the current branch if no argument is provided — then
identifies which docs are affected, classifies needed updates by Diataxis
quadrant, and implements them in a reviewable PR. This skill has no existing
`lrh request` template analog; it fills a gap in the documentation workflow.

## Problem / Context

The existing `lrh request` templates cover auditing and reorganizing docs but
not keeping them current as work lands. After a PR merges, new features may
have no how-to guide, changed APIs may leave stale reference docs, and new
concepts may have no explanation. This work item encodes a post-landing
documentation update workflow that naturally follows the merge → document →
review cycle already present in LRH for code changes.

## Scope

- `SKILL.md`: 11-step execution flow — parse work reference (PR/WI/WS or
  auto-detect from branch), load references, identify scope of completed work,
  map changes to affected docs, classify by Diataxis quadrant, confirm gate,
  create branch, implement updates, validate, open PR, create AD_HOC execution
  record
- `references/diataxis-criteria.md`: per-skill copy of Diataxis criteria
- `references/doc-work-scope.md`: how to identify affected docs from a PR diff,
  work item acceptance criteria, or workstream completion summary; scope rules;
  guidance on PR vs. direct commit for trivial additive changes
- `src/lrh/skills/lrh-doc-work/`: exact package copy for `lrh setup`
- `CLAUDE.md ## Skills` index entry
- No template cross-reference (no existing template counterpart)

## Required Changes

1. Create `src/lrh/skills/lrh-doc-work/SKILL.md`
2. Create `src/lrh/skills/lrh-doc-work/references/diataxis-criteria.md`
3. Create `src/lrh/skills/lrh-doc-work/references/doc-work-scope.md`
4. Copy `src/lrh/skills/lrh-doc-work/` to `.claude/skills/lrh-doc-work/` (byte-for-byte)
5. Add `/lrh-doc-work` entry to `CLAUDE.md ## Skills`
6. Verify `diff -r src/lrh/skills/lrh-doc-work/ .claude/skills/lrh-doc-work/` is empty

## Non-Goals

- Does not update docs in any repository — implements the skill only
- Does not implement `/lrh-doc-audit` or `/lrh-doc-organize`
- Does not add a template to `src/lrh/assist/templates/request/` (no template
  counterpart; cross-reference convention does not apply here)
- Does not upload the skill to the claude.ai Skills API
- Scope of this skill may be refined after `/lrh-doc-audit` and
  `/lrh-doc-organize` are dogfooded

## Acceptance Criteria

- `.claude/skills/lrh-doc-work/SKILL.md` exists with valid frontmatter
- `.claude/skills/lrh-doc-work/` is an exact copy of `src/lrh/skills/lrh-doc-work/`
- `CLAUDE.md ## Skills` has a `/lrh-doc-work` entry
- `lrh validate` passes with 0 errors

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `diff -r src/lrh/skills/lrh-doc-work/ .claude/skills/lrh-doc-work/`
