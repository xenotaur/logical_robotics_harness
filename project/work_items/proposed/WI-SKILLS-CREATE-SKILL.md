---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-CREATE-SKILL
title: Implement create-skill skill and src/lrh/skills/ infrastructure
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
  - project/design/proposals/proposed/lrh-project-local-skills/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - implement_lrh_setup
acceptance:
  - src/lrh/skills/__init__.py exists
  - src/lrh/skills/create-skill/SKILL.md exists with valid frontmatter
  - src/lrh/skills/create-skill/references/ contains lrh-skill-pattern.md, frontmatter-guide.md, worked-example.md
  - .claude/skills/create-skill/ is an exact copy of src/lrh/skills/create-skill/
  - pyproject.toml includes "lrh.skills" package-data entry
  - python -c "import lrh.skills" succeeds
  - CONTRIBUTING.md documents the src/lrh/skills/ <-> .claude/skills/ sync requirement
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/__init__.py
  - src/lrh/skills/create-skill/SKILL.md
  - src/lrh/skills/create-skill/references/lrh-skill-pattern.md
  - src/lrh/skills/create-skill/references/frontmatter-guide.md
  - src/lrh/skills/create-skill/references/worked-example.md
  - .claude/skills/create-skill/SKILL.md
  - .claude/skills/create-skill/references/lrh-skill-pattern.md
  - .claude/skills/create-skill/references/frontmatter-guide.md
  - .claude/skills/create-skill/references/worked-example.md
---

## Summary

Implement Stage 1 of `PROP-LRH-PROJECT-LOCAL-SKILLS`: the `create-skill`
Claude Code skill and the package infrastructure that supports distributing
LRH skills.

## Problem / Context

LRH workflow steps (assess, design, create work items, create workstreams)
are driven by prompts stored in Apple Notes and pasted manually into chat.
This work item establishes the infrastructure for moving that knowledge into
versioned, project-aware Claude Code skills. The `create-skill` skill is
both the first LRH skill and the tool used to bootstrap all future skills.

## Required Changes

1. Create `src/lrh/skills/__init__.py` (empty — makes `lrh.skills` a Python
   package, compatible with `importlib.resources` for Stage 2 `lrh setup`).

2. Create `src/lrh/skills/create-skill/SKILL.md` — the canonical skill body
   following the `new-scenario` reference pattern: frontmatter with
   `disable-model-invocation: true`, 7 execution steps, quality checklist,
   non-goals. Full design is in the linked proposal and design conversation.

3. Create `src/lrh/skills/create-skill/references/` — three reference files:
   - `lrh-skill-pattern.md`: LRH-validated skill structure pattern
   - `frontmatter-guide.md`: official SKILL.md frontmatter field reference
   - `worked-example.md`: `new-scenario` annotated as reference implementation

4. Create `.claude/skills/create-skill/` — exact copy of
   `src/lrh/skills/create-skill/` for self-hosting in the LRH repo
   (auto-discovered by Claude Code without requiring `lrh setup`).

5. Update `pyproject.toml` — add `"lrh.skills" = ["**/*.md"]` to
   `[tool.setuptools.package-data]`.

6. Update `CONTRIBUTING.md` — add a skills section documenting that
   `src/lrh/skills/<name>/` is the canonical source and `.claude/skills/<name>/`
   must be kept in sync in the same PR.

## Non-Goals

- Do not implement `lrh setup` (that is `WI-SKILLS-LRH-SETUP`, Stage 2).
- Do not implement any workflow skills (`/lrh-work-item` etc.) in this item.
- Do not add skill validation to `lrh validate` in this item.
- Do not create a global `~/.claude/skills/` installation.
- Do not add CI diff enforcement between the two skill copies (Stage 3).

## Acceptance Criteria

- `src/lrh/skills/__init__.py` exists
- `src/lrh/skills/create-skill/SKILL.md` exists with valid YAML frontmatter
  (`name: create-skill`, `disable-model-invocation: true`)
- All three `references/` files exist under both `src/lrh/skills/create-skill/`
  and `.claude/skills/create-skill/`
- `src/lrh/skills/create-skill/` and `.claude/skills/create-skill/` are
  byte-for-byte identical
- `pyproject.toml` includes `"lrh.skills" = ["**/*.md"]`
- `python -c "import lrh.skills"` succeeds
- `lrh validate` passes with no errors
- `CONTRIBUTING.md` documents the sync requirement

## Validation Commands

- `lrh validate`
- `python -c "import lrh.skills"`
- `scripts/version tools`

## Risk Notes

- The `.claude/skills/` directory is newly created; Claude Code will require
  a session restart to discover skills in a session where the directory did
  not previously exist.
- Two copies of the skill files must be kept in sync manually until Stage 3
  adds CI enforcement. This is documented in CONTRIBUTING.md.
