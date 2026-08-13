---
execution_id: 2026_08_08_02_22_30_WI_SKILLS_LRH_WORK_REMAINS
prompt_id: PROMPT(AD_HOC:WI_SKILLS_LRH_WORK_REMAINS)[2026-08-08T01:44:33+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/516
commit: 273470f90b874909b80322c6acd1180de38717f6
created_at: 2026-08-08T02:22:30+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILLS-LRH-WORK-REMAINS.md
session_transcript: claude-app:d5c66194-c6cd-489d-8333-23de57f61b50
---

# Summary

Drafted `WI-SKILLS-LRH-WORK-REMAINS`, a work item to implement the
`/lrh-work-remains` Claude Code skill: a read-only, session-scoped reporting
skill grounded in tracked repo state rather than conversational recall. The
design was fleshed out in-session with the user (idea review, best-practices
survey, high-level design, low-level choices, pros/cons vs. best practices)
before this work item was drafted via `/lrh-work-item`.

# Result

Created `project/work_items/proposed/WI-SKILLS-LRH-WORK-REMAINS.md` on branch
`xenotaur/feat/wi-skills-lrh-work-remains`, opened PR #516
(https://github.com/xenotaur/logical_robotics_harness/pull/516). This record
covers only the WI-creation PR; implementation of the skill itself is a
separate, later PR against this work item.

# Validation

- `lrh validate`: 0 errors, 1 pre-existing warning unrelated to this change
  (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on `WS-SESSION-ARCHIVE-SYNC`)

# Follow-up

- Implement the skill itself against `WI-SKILLS-LRH-WORK-REMAINS` (separate
  PR) once this planning PR lands.
- Out of scope here: port the design back to Taurcode's
  `prompts/taurcode/remains.md` and a new `prompts/lrh/lrh-remains.md`,
  tracked separately in that repo.
