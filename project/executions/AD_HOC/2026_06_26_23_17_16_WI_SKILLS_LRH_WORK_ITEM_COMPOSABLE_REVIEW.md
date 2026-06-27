---
execution_id: 2026_06_26_23_17_16_WI_SKILLS_LRH_WORK_ITEM_COMPOSABLE_REVIEW
prompt_id: PROMPT(AD_HOC:WI_SKILLS_LRH_WORK_ITEM_COMPOSABLE_REVIEW)[2026-06-26T23:15:33-04:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_06_26_23_10_06_WI_SKILLS_LRH_WORK_ITEM_COMPOSABLE
pr: https://github.com/xenotaur/logical_robotics_harness/pull/331
commit: 4e9cbc4
created_at: 2026-06-26T23:17:16-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/331
session_transcript: claude-app:local_5d607d17-5c38-4dcf-b83e-ea913d88c9af
---

# Summary

Address 4 reviewer comments (2 distinct issues) on PR #331
(Make /lrh-work-item composable).

# Result

Fixed both issues in `lrh-work-item-workflow.md`:

- **Issue A** (comments 1 & 3, copilot, duplicate): The orchestration section
  said orchestration was "enabled by the `when_to_use` field". Corrected to say
  orchestration is enabled by *removing* `disable-model-invocation: true`;
  `when_to_use` was added to provide guidance that reduces accidental
  auto-invocations.
- **Issue B** (comments 2 & 4, copilot, duplicate): "Claude will not invoke
  this skill…" was an absolute platform guarantee. Softened to "Claude is less
  likely to invoke this skill…" and added explicit note that `when_to_use` is
  guidance, not a hard platform guarantee.

Both edits mirrored to `.claude/skills/lrh-work-item/`.

No comments were skipped.

# Validation

- `diff src/lrh/skills/lrh-work-item/references/lrh-work-item-workflow.md .claude/skills/lrh-work-item/references/lrh-work-item-workflow.md` — no differences
- `lrh validate` — 0 errors, 0 warnings

# Follow-up

- Update `session_transcript: pending` to `claude-app:<session-id>` after
  session ends.
