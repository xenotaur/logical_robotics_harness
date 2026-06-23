---
execution_id: 2026_06_23_12_00_00_LRH_WORK_ITEM_SKILL
prompt_id: PROMPT(WI-SKILLS-LRH-WORK-ITEM:LRH_WORK_ITEM_SKILL)[2026-06-23T12:00:00-07:00]
work_item: WI-SKILLS-LRH-WORK-ITEM
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-06-23T19:00:00+00:00
---

# Summary

Implemented the `lrh-work-item` Claude Code skill using the `/create-skill`
skill (Stage 3 of `WS-SKILLS`). This is the first workflow skill added to
the LRH skills infrastructure established by `WI-SKILLS-CREATE-SKILL`.

# Result

Created the following artifacts:

- `project/work_items/proposed/WI-SKILLS-LRH-WORK-ITEM.md` — formal work
  item record for this deliverable.
- `src/lrh/skills/lrh-work-item/SKILL.md` — canonical 7-step skill body with
  `disable-model-invocation: true`, guided interview, confirm-before-write
  gate, quality checklist, and non-goals section.
- `src/lrh/skills/lrh-work-item/references/work-item-schema.md` — full YAML
  frontmatter field reference including type, action, and evidence vocabularies.
- `src/lrh/skills/lrh-work-item/references/work-item-body-guide.md` —
  section-by-section guide for the work item body, including readiness criteria.
- `src/lrh/skills/lrh-work-item/references/lrh-work-item-workflow.md` —
  lifecycle diagram and relationship to `ready-work-item`,
  `prompt-from-work-item`, and execution records.
- `.claude/skills/lrh-work-item/` — exact self-hosted copy of all four skill
  files, auto-discovered by Claude Code in the LRH repo session.
- `CLAUDE.md` — new file with `## Skills` section listing `/create-skill`
  and `/lrh-work-item`.
- `project/workstreams/proposed/WS-SKILLS.md` — added `WI-SKILLS-LRH-WORK-ITEM`
  to the `work_items:` list.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `diff -r src/lrh/skills/lrh-work-item/ .claude/skills/lrh-work-item/`: identical.

# Follow-up

- Restart the Claude Code session to discover `.claude/skills/lrh-work-item/`
  in the current session (the directory is new to this session).
- `WI-SKILLS-LRH-SETUP`: implement `lrh setup` to copy skills to
  `~/.claude/skills/` for global availability (Stage 2).
- Future workflow skills (`/lrh-workstream`, `/lrh-assess`) can be created
  using `/create-skill` once this PR is merged.
