---
execution_id: 2026_06_22_12_00_00_CREATE_SKILL_INFRASTRUCTURE
prompt_id: PROMPT(WI-SKILLS-CREATE-SKILL:CREATE_SKILL_INFRASTRUCTURE)[2026-06-22T12:00:00-07:00]
work_item: WI-SKILLS-CREATE-SKILL
status: landed
rerun_of:
pr:
commit:
created_at: 2026-06-22T19:00:00+00:00
---

# Summary

Implemented Stage 1 of `PROP-LRH-PROJECT-LOCAL-SKILLS`: the `create-skill`
Claude Code skill and the `src/lrh/skills/` package infrastructure.

# Result

Created the following artifacts:

- `project/workstreams/proposed/WS-SKILLS.md` — new workstream grouping all
  skills-related work items.
- `project/work_items/proposed/WI-SKILLS-CREATE-SKILL.md` — formal work item
  record for this deliverable.
- `src/lrh/skills/__init__.py` — empty init making `lrh.skills` a Python
  package, compatible with `importlib.resources` for future `lrh setup`.
- `src/lrh/skills/create-skill/SKILL.md` — canonical 7-step skill body with
  `disable-model-invocation: true`, confirm-before-write gate, quality
  checklist, and non-goals section.
- `src/lrh/skills/create-skill/references/lrh-skill-pattern.md` — LRH skill
  structure pattern and conventions.
- `src/lrh/skills/create-skill/references/frontmatter-guide.md` — official
  SKILL.md frontmatter field reference.
- `src/lrh/skills/create-skill/references/worked-example.md` — `new-scenario`
  skill annotated as reference implementation with design contrast table.
- `.claude/skills/create-skill/` — exact self-hosted copy of all four skill
  files, auto-discovered by Claude Code in the LRH repo session.
- `pyproject.toml` — added `"lrh.skills" = ["**/*.md"]` to package-data.
- `CONTRIBUTING.md` — added skills section documenting the sync requirement
  between `src/lrh/skills/<name>/` and `.claude/skills/<name>/`.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `python -c "import lrh.skills"`: succeeded.
- `diff -r src/lrh/skills/create-skill/ .claude/skills/create-skill/`: identical.

# Follow-up

- `WI-SKILLS-LRH-SETUP`: implement `lrh setup` to copy skills to
  `~/.claude/skills/` for global availability (Stage 2).
- A session restart in the LRH repo is required for Claude Code to discover
  the newly created `.claude/skills/` directory.
- Future workflow skills (`/lrh-work-item`, `/lrh-workstream`, `/lrh-assess`)
  can now be created using `/create-skill` once the session is restarted.
