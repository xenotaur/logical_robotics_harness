---
execution_id: 2026_08_19_22_15_28_ADOPT_PROP_LRH_MEMORY_COMMAND
prompt_id: PROMPT(AD_HOC:ADOPT_PROP_LRH_MEMORY_COMMAND)[2026-08-19T22:15:18+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/568
commit: 059c003066c18319cf1718c7a709d9bd5dca9eca
created_at: 2026-08-19T22:15:28+00:00
agent: claude_app
instruction_source: project/design/proposals/adopted/lrh-memory-command/00_proposal.md
session_transcript: claude-app:3bfe1290-c27a-4ffe-82f5-e718adbd8319
---

# Summary

Adopted `PROP-LRH-MEMORY-COMMAND`: moved `project/design/proposals/proposed/lrh-memory-command/` to `adopted/`, per user instruction to move it to adopted before executing the first work item.

# Result

- Edited `00_proposal.md` frontmatter: `status: proposed` → `adopted`,
  `updated_on: 2026-08-19`. `implementation_status` left `not_started` —
  adoption governs the design decision, not implementation completion;
  none of the four work items have been implemented yet.
- `git mv`'d the proposal directory from `proposed/` to `adopted/`.
- Updated `related_design:` path references and body citations in the
  workstream (`WS-LRH-MEMORY-COMMAND.md`) and all four work items
  (`WI-LRH-MEMORY-WRITE-SIDE`/`ARCHIVE-SIDE`/`READ-SIDE`/`PORTABILITY`)
  to point at the new `adopted/` location.
- Left the two historical execution records that cite the old `proposed/`
  path untouched — they document what was true when written, not current
  state.
- Pushed as commit (see `commit:` below), opened as PR #568.

This satisfies the entry-gate the workstream's own Purpose section and
each work item's Non-Goals require before any of them proceeds to
`/lrh-implement`.

# Validation

`lrh validate` — 0 errors, 0 warnings. `git grep "proposals/proposed/lrh-memory-command"` confirmed only the two intentionally-untouched historical execution records remain.

# Follow-up

- Proceed with `/lrh-land` for PR #568.
- Once merged, `/lrh-execute WI-LRH-MEMORY-WRITE-SIDE` (the first work
  item in `WS-LRH-MEMORY-COMMAND`, no `depends_on`) becomes unblocked
  per the entry-gate this adoption satisfies.
