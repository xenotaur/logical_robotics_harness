---
execution_id: 2026_06_26_22_39_38_WI_SKILLS_LRH_WORKSTREAM
prompt_id: PROMPT(WI-SKILLS-LRH-WORKSTREAM:WI_SKILLS_LRH_WORKSTREAM)[2026-06-26T22:31:50-04:00]
work_item: WI-SKILLS-LRH-WORKSTREAM
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/330
commit: f5feabd
created_at: 2026-06-26T22:39:38-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILLS-LRH-WORKSTREAM.md
session_transcript: pending
---

# Summary

Implement the `/lrh-workstream` Claude Code skill that guides users through
creating a workstream planning node at
`project/workstreams/proposed/<WS-ID>.md` following the LRH workstream
schema.

# Result

Created `src/lrh/skills/lrh-workstream/` with:

- `SKILL.md` — 9-step skill with interview, research, confirm gate, write,
  validate, and follow-on-offer steps; `disable-model-invocation: true`,
  `argument-hint: [WS-ID]`; Step 9 offers to link existing work items and
  invoke `/lrh-work-item` for new ones
- `references/workstream-schema.md` — frontmatter field reference grounded
  in validator constants (`WORKSTREAM_REQUIRED_FIELDS`, `WORKSTREAM_KINDS`,
  `WORKSTREAM_STATUS`, `WORKSTREAM_STAGE`, `WORKSTREAM_LIST_FIELDS`); notes
  that `WS-*` is a convention, not a schema-enforced constraint
- `references/workstream-body-guide.md` — section guide for Purpose, Scope,
  Work Items, Exit Criteria, and Non-Goals

Mirrored all three files to `.claude/skills/lrh-workstream/`. Added
`/lrh-workstream` entry to `CLAUDE.md` `## Skills` index.

# Validation

- `scripts/version tools` — Black 26.3.1, Ruff 0.15.12 confirmed
- `lrh validate` — 0 errors, 0 warnings
- `diff -r src/lrh/skills/lrh-workstream/ .claude/skills/lrh-workstream/` — no differences

# Follow-up

- Update `session_transcript: pending` to `claude-app:<session-id>` after
  session ends.
- Merge PR, then move WI-SKILLS-LRH-WORKSTREAM to `resolved/` with
  `resolution: implemented`.
- Implement WI-SKILLS-LRH-WORK-ITEM-COMPOSABLE (no dependencies; can start now).
- Implement WI-SKILLS-LRH-DESIGN-STEP4 after both this and
  WI-SKILLS-LRH-WORK-ITEM-COMPOSABLE land.
