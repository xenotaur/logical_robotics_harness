---
execution_id: 2026_06_26_13_44_20_WI_SKILLS_LRH_PROPOSAL
prompt_id: PROMPT(WI-SKILLS-LRH-PROPOSAL:WI_SKILLS_LRH_PROPOSAL)[2026-06-26T13:31:29-04:00]
work_item: WI-SKILLS-LRH-PROPOSAL
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/329
commit: 4189549
created_at: 2026-06-26T13:44:20-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILLS-LRH-PROPOSAL.md
session_transcript: claude-app:5d607d17-5c38-4dcf-b83e-ea913d88c9af
---

# Summary

Implement the `/lrh-proposal` Claude Code skill that guides users through
creating a design proposal document at
`project/design/proposals/proposed/<slug>/00_proposal.md` following the LRH
proposal schema.

# Result

Created `src/lrh/skills/lrh-proposal/` with:

- `SKILL.md` — skill with interview, research, confirm gate, write, validate,
  and follow-on-offer steps; `disable-model-invocation: true`,
  `argument-hint: [slug]`
- `references/proposal-schema.md` — YAML frontmatter field reference derived
  from `src/lrh/control/validator.py` constants (`DESIGN_PROPOSAL_STATUS`,
  `DESIGN_PROPOSAL_IMPLEMENTATION_STATUS`, `DESIGN_PROPOSAL_LIST_FIELDS`) and
  `project/design/proposals/README.md`
- `references/proposal-body-guide.md` — section authoring guide for Summary,
  Background/Motivation, Design Decisions, Non-Goals, and Implementation Plan

Mirrored all three files to `.claude/skills/lrh-proposal/`. Added
`/lrh-proposal` entry to `CLAUDE.md` `## Skills` index.

# Validation

- `scripts/version tools` — Black 26.3.1, Ruff 0.15.12 confirmed
- `lrh validate` — 0 errors, 0 warnings
- `diff -r src/lrh/skills/lrh-proposal/ .claude/skills/lrh-proposal/` — no differences

# Follow-up

- Update `session_transcript: pending` to `claude-app:<session-id>` after
  session ends.
- Merge PR, then move WI-SKILLS-LRH-PROPOSAL to `resolved/` with
  `resolution: implemented`.
- Implement WI-SKILLS-LRH-WORKSTREAM (no dependencies; can start now).
- Implement WI-SKILLS-LRH-WORK-ITEM-COMPOSABLE (no dependencies; can start now).
- Implement WI-SKILLS-LRH-DESIGN-STEP4 after both above land.
