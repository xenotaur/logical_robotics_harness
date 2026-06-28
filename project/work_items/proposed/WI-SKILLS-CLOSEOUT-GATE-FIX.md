---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-CLOSEOUT-GATE-FIX
title: Improve /lrh-closeout confirm gate to surface WS exit criteria
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-SKILLS-CLOSEOUT
related_design:
  - project/design/proposals/adopted/lrh-closeout/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
acceptance: []
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected: []
---

## Summary

Update `/lrh-closeout` Step 2 (assess state) and Step 4 (confirm gate) to
display the full `exit_criteria:` list from the workstream file and require
explicit human confirmation that each criterion is met before offering WS
closeout. The current structural check (`work_items:` all resolved) is
necessary but not sufficient.

## Problem / Context

`WS-SKILLS-CLOSEOUT` was closed prematurely (2026-06-27) because the
structural check passed: all WIs in `work_items:` were resolved. But the
WS exit criteria explicitly required `WI-PROMPT-CLI-CLOSEOUT` (Phase 2),
which was not in `work_items:` (it didn't exist yet) and was not displayed
at the confirm gate.

The confirm gate noted "exit criteria include WI-PROMPT-CLI-CLOSEOUT" but
did not display the full criteria list or require per-criterion confirmation,
so the user accepted without friction. This gap was identified in the
2026-06-27 closeout session and captured in feedback memory
`feedback_closeout_ws_exit_criteria`.

## Required Changes

TODO: flesh out with `lrh request ready-work-item`. Key changes expected:
- In `src/lrh/skills/lrh-closeout/SKILL.md` Step 2, add: read and display
  `exit_criteria:` list when assessing WS readiness
- In `src/lrh/skills/lrh-closeout/SKILL.md` Step 4 confirm gate, add: for
  each WS exit criterion, show it and ask user to confirm it is met before
  proceeding with WS closeout
- Update `src/lrh/skills/lrh-closeout/references/closeout-workflow.md`
  WS Closeout Protocol readiness check section accordingly
- Mirror changes to `.claude/skills/lrh-closeout/`

## Non-Goals

- Does not add machine-parseable enforcement of exit criteria (prose criteria
  are human-authored and may not be checkable by tooling)
- Does not change the `work_items:` structural check — it remains a
  necessary precondition; exit criteria confirmation is additive

## Acceptance Criteria

TODO: flesh out with `lrh request ready-work-item`.

## Validation

- `lrh validate`
- `diff -r src/lrh/skills/lrh-closeout/ .claude/skills/lrh-closeout/`
