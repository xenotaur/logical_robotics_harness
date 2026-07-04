---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-LRH-WORK-AUDIT
title: Implement lrh-work-audit Claude Code skill
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design: []
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - mutate_work_items
  - invoke_lrh_closeout
  - implement_audit_work_items_template
acceptance:
  - src/lrh/skills/lrh-work-audit/SKILL.md exists with valid frontmatter
  - .claude/skills/lrh-work-audit/ directory tree is an exact mirror of src/lrh/skills/lrh-work-audit/
  - SKILL.md contains a cross-reference comment pointing to src/lrh/assist/templates/request/audit_work_items.md
  - CLAUDE.md ## Skills section has a /lrh-work-audit entry
  - lrh validate passes with 0 errors
  - diff -r src/lrh/skills/lrh-work-audit/ .claude/skills/lrh-work-audit/ is clean
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-work-audit/SKILL.md
  - src/lrh/skills/lrh-work-audit/references/drift-detection-lens.md
  - src/lrh/skills/lrh-work-audit/references/pr-tracing-and-scoring.md
  - .claude/skills/lrh-work-audit/SKILL.md
  - .claude/skills/lrh-work-audit/references/drift-detection-lens.md
  - .claude/skills/lrh-work-audit/references/pr-tracing-and-scoring.md
---

## Summary

Create a `/lrh-work-audit` Claude Code skill that surveys open work items, scores
them for priority, and identifies drift between declared state and repository
reality — the same structured-audit pattern used by `/lrh-doc-audit`.

## Problem / Context

The codebase has no systematic tool for surveying open work items. Without a
dedicated skill, an agent must manually query `lrh work-items audit`, compare
declared status against git history and open PRs, and construct a priority
ranking — a multi-step, error-prone process that varies across sessions. The
`/lrh-doc-audit` skill demonstrates that capturing this pattern as a reusable
skill produces consistent, reviewable artifacts.

The `lrh request assess-repository --scope work_item` surface already performs
single-item drift detection; this skill adds batch coverage, priority scoring,
and orphaned-PR forensics on top of it.

## Scope

Create the skill source tree under `src/lrh/skills/lrh-work-audit/` and mirror
it to `.claude/skills/lrh-work-audit/`. Add a `/lrh-work-audit` entry to
`CLAUDE.md`. Do not implement the companion `lrh request audit-work-items`
template in this work item (tracked separately in WI-TEMPLATE-AUDIT-WORK-ITEMS).

## Required Changes

- Create `src/lrh/skills/lrh-work-audit/SKILL.md` — the skill definition,
  including frontmatter, three-phase execution instructions (design, instruction,
  execution), and a `<!-- Template counterpart -->` cross-reference comment
  pointing to `src/lrh/assist/templates/request/audit_work_items.md`.
- Create `src/lrh/skills/lrh-work-audit/references/drift-detection-lens.md` —
  explains the three-lens audit frame (Repo Reality, Declared State, Alignment
  and Drift) drawn from `lrh request assess-repository --scope work_item`.
- Create `src/lrh/skills/lrh-work-audit/references/pr-tracing-and-scoring.md` —
  explains how to trace orphaned execution records to merged PRs via `git log
  --grep` and `gh pr view`, and how to score items for priority.
- Mirror the complete skill tree to `.claude/skills/lrh-work-audit/` so Claude
  Code discovers it.
- Add `/lrh-work-audit` to the `## Skills` section of `CLAUDE.md`.

## Acceptance Criteria

- `src/lrh/skills/lrh-work-audit/SKILL.md` exists with valid frontmatter.
- `.claude/skills/lrh-work-audit/` directory tree is an exact mirror of `src/lrh/skills/lrh-work-audit/`.
- `SKILL.md` contains a `<!-- Template counterpart -->` comment referencing
  `src/lrh/assist/templates/request/audit_work_items.md`.
- `CLAUDE.md` `## Skills` section lists `/lrh-work-audit`.
- `lrh validate` passes with 0 errors.
- `diff -r src/lrh/skills/lrh-work-audit/ .claude/skills/lrh-work-audit/` is
  clean (no differences).

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `diff -r src/lrh/skills/lrh-work-audit/ .claude/skills/lrh-work-audit/`

## Non-Goals

- Do not implement `lrh request audit-work-items` or any Python template/renderer
  (tracked in WI-TEMPLATE-AUDIT-WORK-ITEMS).
- Do not implement any `lrh work-items` CLI changes.
- Do not create a workstream; WS-SKILLS and WS-SKILLS-DOC are already closed.

## Design Notes

Model this skill on the `/lrh-doc-audit` pattern:
- `lrh-doc-audit` invokes `lrh request audit_docs` → `/lrh-work-audit` will
  invoke `lrh request audit-work-items` (once that template exists).
- The skill SKILL.md cross-references the template with a `<!-- Template
  counterpart -->` comment; the template references back with `<!-- Skill
  reference -->`.
- Reference files under `references/` provide the audit lenses and scoring
  heuristics that guide the skill's execution phase.

Key audit outputs the skill should produce:
1. Drift table: each proposed WI mapped to Repo Reality / Declared State /
   Alignment verdict.
2. Priority ranking: scores for importance, feasibility, technical risk, and
   whether the WI blocks or enables others.
3. Orphaned-record forensics: stale `in_progress` execution records with no
   `pr:` field traced to their actual merged PRs (or flagged as truly orphaned).
