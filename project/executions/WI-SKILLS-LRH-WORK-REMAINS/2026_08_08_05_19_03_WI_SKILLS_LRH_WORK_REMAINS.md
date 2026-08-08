---
execution_id: 2026_08_08_05_19_03_WI_SKILLS_LRH_WORK_REMAINS
prompt_id: PROMPT(WI-SKILLS-LRH-WORK-REMAINS:WI_SKILLS_LRH_WORK_REMAINS)[2026-08-08T05:08:59+00:00]
work_item: WI-SKILLS-LRH-WORK-REMAINS
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/521
commit: 
created_at: 2026-08-08T05:19:03+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILLS-LRH-WORK-REMAINS.md
session_transcript: claude-app:d5c66194-c6cd-489d-8333-23de57f61b50
---

# Summary

Implemented the `/lrh-work-remains` Claude Code skill per
`WI-SKILLS-LRH-WORK-REMAINS`: a strictly read-only, session-scoped
reporting skill grounded in tracked repo state per a fixed 18-item
checklist.

# Result

Created `src/lrh/skills/lrh-work-remains/SKILL.md` +
`references/remains-checklist.md` + `references/grounding-sources.md`,
mirrored byte-for-byte to `.claude/skills/lrh-work-remains/`, and added a
`CLAUDE.md ## Skills` index entry. Opened PR #521
(https://github.com/xenotaur/logical_robotics_harness/pull/521) on branch
`xenotaur/feat/wi-skills-lrh-work-remains-impl` (branch name carries an
`-impl` suffix to avoid colliding with the already-merged
`WI-SKILLS-LRH-WORK-REMAINS` WI-creation branch of the same base name).

Diff-mode `/lrh-self-review` ran before the push (per `/lrh-implement`
Step 7.5): clean, no findings — see
`project/executions/AD_HOC/2026_08_08_05_17_47_WI_SKILLS_LRH_WORK_REMAINS_SELFREVIEW.md`.

# Validation

- `scripts/version tools`, `scripts/format --check --diff`, `scripts/lint`:
  clean (required reinstalling pinned `black`/`ruff` via
  `pip install -c constraints-dev.txt black ruff` — the environment had
  drifted to unpinned versions)
- `scripts/test`: 1051 tests passed, release smoke passed
- `lrh validate`: 0 errors, 1 pre-existing warning unrelated to this change
  (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on `WS-SESSION-ARCHIVE-SYNC`)
- `diff -r src/lrh/skills/lrh-work-remains/ .claude/skills/lrh-work-remains/`:
  identical

# Follow-up

- Land via `/lrh-land` (review-response, confirm-fixes, merge, closeout).
- Out of scope here: Taurcode-repo prompt port-back, tracked separately in
  that repo.
