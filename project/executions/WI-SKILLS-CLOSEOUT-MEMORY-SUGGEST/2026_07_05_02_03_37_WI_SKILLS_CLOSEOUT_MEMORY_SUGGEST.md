---
execution_id: 2026_07_05_02_03_37_WI_SKILLS_CLOSEOUT_MEMORY_SUGGEST
prompt_id: PROMPT(WI-SKILLS-CLOSEOUT-MEMORY-SUGGEST:WI_SKILLS_CLOSEOUT_MEMORY_SUGGEST)[2026-07-05T01:55:24-04:00]
work_item: WI-SKILLS-CLOSEOUT-MEMORY-SUGGEST
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/373
commit: 7637db7664b1559b4c49b059e7779af39a1c16fc
created_at: 2026-07-05T02:03:37-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILLS-CLOSEOUT-MEMORY-SUGGEST.md
session_transcript: claude-app:5d2f21ba-4fa7-44f2-b4f1-69a8becf1b97
---

# Summary

Implemented `WI-SKILLS-CLOSEOUT-MEMORY-SUGGEST`: restructured `/lrh-closeout`
Step 7 to review the session and draft candidate memory suggestions (or
state none found) before asking the user, instead of a blind question.

# Result

- Edited `src/lrh/skills/lrh-closeout/SKILL.md` Step 7: now reviews the
  session's changes/decisions against the memory criteria (surprising,
  non-obvious, durable, not derivable from code/git history), drafts 0-3
  candidates (rule plus one-line why each) or states explicitly that none
  were found, then presents an explicit confirm/edit/decline gate before
  anything is written.
- Mirrored to `.claude/skills/lrh-closeout/SKILL.md` (verified byte-identical).
- Left `project/design/proposals/adopted/lrh-closeout/00_proposal.md`,
  `references/closeout-workflow.md`, and the Quality Checklist untouched,
  per the work item's non-goals.

# Validation

- `scripts/format --check --diff` — clean, 175 files unchanged
- `scripts/lint` — all checks passed
- `scripts/test` — 696 tests, OK
- `lrh validate` — 0 errors, 0 warnings
- `diff -r src/lrh/skills/lrh-closeout/ .claude/skills/lrh-closeout/` — identical

# Follow-up

- `session_transcript: pending` — update to `claude-app:<session-id>`
  before archiving this session.
- Next real invocation of `/lrh-closeout` will exercise the new Step 7
  behavior for the first time in practice.
