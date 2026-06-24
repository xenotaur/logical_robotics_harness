---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-LRH-WORK-ITEM
title: Implement lrh-work-item Claude Code skill
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-SKILLS
related_design:
  - project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md
depends_on:
  - WI-SKILLS-CREATE-SKILL
blocked_by: []
expected_actions:
  - create_file
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - implement_lrh_setup
  - implement_refine_mode
acceptance:
  - src/lrh/skills/lrh-work-item/SKILL.md exists with valid frontmatter
  - src/lrh/skills/lrh-work-item/references/ contains work-item-schema.md, work-item-body-guide.md, lrh-work-item-workflow.md
  - .claude/skills/lrh-work-item/ is an exact copy of src/lrh/skills/lrh-work-item/
  - lrh validate passes with 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-work-item/SKILL.md
  - src/lrh/skills/lrh-work-item/references/work-item-schema.md
  - src/lrh/skills/lrh-work-item/references/work-item-body-guide.md
  - src/lrh/skills/lrh-work-item/references/lrh-work-item-workflow.md
  - .claude/skills/lrh-work-item/SKILL.md
  - .claude/skills/lrh-work-item/references/work-item-schema.md
  - .claude/skills/lrh-work-item/references/work-item-body-guide.md
  - .claude/skills/lrh-work-item/references/lrh-work-item-workflow.md
  - CLAUDE.md (Skills section updated)
---

## Summary

Implement the `lrh-work-item` Claude Code skill that guides users through
creating new LRH work items interactively. The skill interviews the user,
researches related workstreams and focus, proposes a complete frontmatter and
body, confirms before writing, then validates with `lrh validate`.

## Problem / Context

Work items are currently authored manually with no guided structure. Thin items
missing key sections (Scope, Required Changes, Acceptance Criteria, Validation)
fail `lrh request prompt-from-work-item` readiness checks and require
an additional `lrh request ready-work-item` pass. A guided skill that produces
complete, prompt-ready items from the start reduces this friction.

`WI-SKILLS-CREATE-SKILL` (now merged as PR #314) established the skill
infrastructure (`src/lrh/skills/`, `.claude/skills/`, `pyproject.toml`
package-data). This item adds the first workflow skill to that infrastructure.

## Scope

- Implement `src/lrh/skills/lrh-work-item/` with SKILL.md and three
  references files, and mirror byte-for-byte to `.claude/skills/lrh-work-item/`
- Create work item, workstream update, and execution record in `project/`
- Create `CLAUDE.md` with a Skills index listing `/create-skill` and
  `/lrh-work-item`

## Required Changes

1. Create `src/lrh/skills/lrh-work-item/SKILL.md` — 7-step guided skill with
   `disable-model-invocation: true` and a mandatory confirm-before-write gate.

2. Create three `references/` files under `src/lrh/skills/lrh-work-item/`:
   - `work-item-schema.md` — YAML frontmatter field reference, type vocabulary,
     action vocabulary, evidence vocabulary.
   - `work-item-body-guide.md` — Section-by-section authoring guide for the
     work item body.
   - `lrh-work-item-workflow.md` — Lifecycle context and relationship to
     `ready-work-item`, `prompt-from-work-item`, and execution records.

3. Mirror all four files to `.claude/skills/lrh-work-item/` (byte-for-byte
   identical, verified with `diff -r`).

4. Add `WI-SKILLS-LRH-WORK-ITEM` to the `work_items:` list in
   `project/workstreams/proposed/WS-SKILLS.md`.

5. Create or update `CLAUDE.md` with a `## Skills` section listing both
   `/create-skill` and `/lrh-work-item`.

## Non-Goals

- Do not implement a "refine existing work item" mode — use
  `lrh request ready-work-item` for that.
- Do not implement `lrh setup` — that is `WI-SKILLS-LRH-SETUP`.
- Do not add CI diff enforcement between the two skill copies — that is
  a Stage 3 item in `WS-SKILLS`.
- Do not add skill validation to `lrh validate` in this item.
- Do not create a global `~/.claude/skills/` installation.

## Acceptance Criteria

- `src/lrh/skills/lrh-work-item/SKILL.md` exists with valid YAML frontmatter
  (`name: lrh-work-item`, `disable-model-invocation: true`).
- All three `references/` files exist under both `src/lrh/skills/lrh-work-item/`
  and `.claude/skills/lrh-work-item/`.
- `src/lrh/skills/lrh-work-item/` and `.claude/skills/lrh-work-item/` are
  byte-for-byte identical.
- `lrh validate` passes with 0 errors.
- `CLAUDE.md` lists `/lrh-work-item` in the Skills section.

## Validation

- `scripts/version tools`
- `lrh validate`
- `diff -r src/lrh/skills/lrh-work-item/ .claude/skills/lrh-work-item/`

## Risk Notes

- The skill proposes but does not enforce schema completeness — thin items
  can still be produced if the user accepts a minimal proposal. This is
  intentional: the skill's purpose is guided creation, not forced completeness.
- Two copies must be kept in sync manually until Stage 3 adds CI enforcement.
  This is already documented in `CONTRIBUTING.md`.
