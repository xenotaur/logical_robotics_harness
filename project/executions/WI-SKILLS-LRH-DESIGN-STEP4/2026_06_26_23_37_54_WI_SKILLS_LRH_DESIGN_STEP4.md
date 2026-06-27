---
execution_id: 2026_06_26_23_37_54_WI_SKILLS_LRH_DESIGN_STEP4
prompt_id: PROMPT(WI-SKILLS-LRH-DESIGN-STEP4:WI_SKILLS_LRH_DESIGN_STEP4)[2026-06-26T23:35:06-04:00]
work_item: WI-SKILLS-LRH-DESIGN-STEP4
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/332
commit: 
created_at: 2026-06-26T23:37:54-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILLS-LRH-DESIGN-STEP4.md
session_transcript: pending
---

# Summary

Update `/lrh-design` Step 4 to replace the generic follow-on offer with a
scope-assessment sub-step containing a decision matrix that selects the right
combination of `/lrh-proposal`, `/lrh-workstream`, and `/lrh-work-item` based
on the design's scale and complexity.

# Result

Edited `src/lrh/skills/lrh-design/SKILL.md`:
- Replaced Step 4 "Offer follow-on" with "Assess scope and offer follow-on"
- Added 3-row decision matrix: single PR → /lrh-work-item only; multiple
  PRs/novel decisions → /lrh-proposal ± /lrh-workstream ± /lrh-work-item;
  complex multi-stage → /lrh-proposal + /lrh-workstream first, work items later
- Added per-skill guidance bullets explaining when each artifact is appropriate
- Closing instruction: state recommendation and rationale, wait for user
  confirmation before invoking anything
- Updated Quality Checklist bullet to match new Step 4 description

Mirrored to `.claude/skills/lrh-design/SKILL.md` (identical, diff clean).

# Validation

- `scripts/version tools` — Black 26.3.1, Ruff 0.15.12 confirmed
- `lrh validate` — 0 errors, 0 warnings
- `diff src/lrh/skills/lrh-design/SKILL.md .claude/skills/lrh-design/SKILL.md` — no differences
- Line count: 163 (under 500)

# Follow-up

- Update `session_transcript: pending` to `claude-app:<session-id>` after
  session ends.
- Merge PR, then move WI-SKILLS-LRH-DESIGN-STEP4 to `resolved/` with
  `resolution: implemented`.
- All four design-capture work items from batch (WI-SKILLS-LRH-PROPOSAL,
  WI-SKILLS-LRH-WORKSTREAM, WI-SKILLS-LRH-WORK-ITEM-COMPOSABLE,
  WI-SKILLS-LRH-DESIGN-STEP4) will then be complete.
