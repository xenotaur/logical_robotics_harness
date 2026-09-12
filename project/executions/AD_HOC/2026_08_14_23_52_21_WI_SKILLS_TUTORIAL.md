---
execution_id: 2026_08_14_23_52_21_WI_SKILLS_TUTORIAL
prompt_id: PROMPT(AD_HOC:WI_SKILLS_TUTORIAL)[2026-08-14T23:31:00+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/558
commit: 364b994b
created_at: 2026-08-14T23:52:21+00:00
agent: claude-code
instruction_source: project/work_items/proposed/WI-SKILLS-TUTORIAL.md
session_transcript: claude-app:2e2d17d8-1e0b-4166-bd0a-3df08ec48bdc
---

# Summary

Created `WI-SKILLS-TUTORIAL`, a planning-only work item capturing a design
(produced via `/lrh-design`) for a new beginner tutorial,
`docs/tutorials/using-claude-code-skills.md`, teaching how to invoke an LRH
Claude Code skill, read a confirm-before-write gate, and distinguish a
report-only skill (`/lrh-work-remains`) from one that writes files
(`/lrh-work-item`), while deferring chain-authorization mechanics to a
future tutorial.

# Result

Wrote `project/work_items/proposed/WI-SKILLS-TUTORIAL.md` with full
frontmatter and body (Summary, Problem/Context with prior-art verdicts,
Scope, Required Changes, Non-Goals, Acceptance Criteria, Validation, Risk
Notes). Prior-art check (Step 3 of `/lrh-design` and `/lrh-work-item`) found
no in-repo duplicate and no existing WI/proposal/backlog demand for this
tutorial. Committed on branch `xenotaur/feat/wi-skills-tutorial` and opened
PR #558. This PR creates the work item only — it does not implement the
tutorial itself.

# Validation

- `lrh validate` — 0 errors, 1 pre-existing warning unrelated to this change
  (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on
  `WS-SESSION-ARCHIVE-SYNC`, not touched by this PR).

# Follow-up

- Implement the tutorial itself against this work item (a future
  `/lrh-implement WI-SKILLS-TUTORIAL` run).
- No workstream update was offered or needed — `related_workstreams` is
  empty by design (standalone, well-bounded item).
- `/lrh-design`'s conversation also flagged a possible future explanation
  doc for the `disable-model-invocation`/`when_to_use` invocation-tiering
  rationale, and a possible future tutorial covering chain-authorization
  (`/lrh-land`, `/lrh-execute`) — neither is scoped by this work item and
  both remain open ideas, not tracked backlog entries.
