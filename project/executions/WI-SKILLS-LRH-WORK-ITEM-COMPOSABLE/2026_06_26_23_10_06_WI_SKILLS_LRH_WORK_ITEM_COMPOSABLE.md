---
execution_id: 2026_06_26_23_10_06_WI_SKILLS_LRH_WORK_ITEM_COMPOSABLE
prompt_id: PROMPT(WI-SKILLS-LRH-WORK-ITEM-COMPOSABLE:WI_SKILLS_LRH_WORK_ITEM_COMPOSABLE)[2026-06-26T23:07:12-04:00]
work_item: WI-SKILLS-LRH-WORK-ITEM-COMPOSABLE
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/331
commit: acd8f7b
created_at: 2026-06-26T23:10:06-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILLS-LRH-WORK-ITEM-COMPOSABLE.md
session_transcript: pending
---

# Summary

Make `/lrh-work-item` composable by removing `disable-model-invocation: true`
and replacing it with a `when_to_use` field, and document the orchestration
use case in `lrh-work-item-workflow.md`.

# Result

Edited `src/lrh/skills/lrh-work-item/SKILL.md`:
- Removed `disable-model-invocation: true` line.
- Added `when_to_use` field naming `/lrh-design`, `/lrh-proposal`, and
  `/lrh-workstream` as orchestrating callers and restricting auto-trigger to
  explicit work item creation contexts.

Edited `src/lrh/skills/lrh-work-item/references/lrh-work-item-workflow.md`:
- Added "Orchestration" section explaining which skills may invoke
  `/lrh-work-item`, why the Step 4 confirm gate is sufficient write
  protection per OWASP LLM08, and the subagent preloading consideration.

Both files mirrored to `.claude/skills/lrh-work-item/`. Step 4 confirm gate
text unchanged.

# Validation

- `scripts/version tools` — Black 26.3.1, Ruff 0.15.12 confirmed
- `lrh validate` — 0 errors, 0 warnings
- `diff src/lrh/skills/lrh-work-item/SKILL.md .claude/skills/lrh-work-item/SKILL.md` — no differences
- `diff src/lrh/skills/lrh-work-item/references/lrh-work-item-workflow.md .claude/skills/lrh-work-item/references/lrh-work-item-workflow.md` — no differences

# Follow-up

- Update `session_transcript: pending` to `claude-app:<session-id>` after
  session ends.
- Merge PR, then move WI-SKILLS-LRH-WORK-ITEM-COMPOSABLE to `resolved/`
  with `resolution: implemented`.
- WI-SKILLS-LRH-DESIGN-STEP4 is now unblocked (both predecessor work items
  have landed).
