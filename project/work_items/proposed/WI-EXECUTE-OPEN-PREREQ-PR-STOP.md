---
resolution: null
blocked_reason: null
blocked: false
id: WI-EXECUTE-OPEN-PREREQ-PR-STOP
title: "Make /lrh-execute stop with a structured Immediate-next-action report when an open prerequisite lifecycle PR blocks the target WI"
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design: []
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - modify_lrh_implement
  - redesign_shared_next_step_contract
acceptance:
  - "Given a WI-ID whose file exists on origin/main with a status other than proposed, and an open PR modifying that file, /lrh-execute Step 1 stops before readiness, prior-art, prompt minting, or Step 2, and reports 'Immediate next action: /lrh-land <PR>'"
  - "The existing creation-PR case (file absent from origin/main) uses the same structured stop report"
  - "The stop report uses Immediate next action / Why / After that; the later /lrh-execute command appears only inline as a non-actionable after-merge step, never in a standalone code block or labelled 'next step'"
  - "For a WS-ID, an open-prerequisite candidate is skipped as ineligible and evaluation continues; if no candidate is ready, the stop report names the blocking PR(s) of skipped candidates"
  - "No prompt ID is minted on a Step 1 stop; the stop is recorded as 'stopped' in the Step 5 run journal"
  - "A regression test covers the open-prerequisite case for WI-ID and WS-ID and asserts the src, .claude and .agents skill copies are consistent"
  - "Existing valid /lrh-execute flows are unchanged; all chain-authorization and merge gates are untouched"
  - "scripts/format, scripts/lint, scripts/test and lrh validate pass"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/skills/lrh-execute/SKILL.md
  - src/lrh/skills/lrh-execute/references/creation-pr-check.md
  - ".claude/skills/lrh-execute/ and .agents/skills/lrh-execute/ mirrors"
  - a new regression test under tests/
---

# Make /lrh-execute stop with a structured Immediate-next-action report when an open prerequisite lifecycle PR blocks the target WI

## Summary

`/lrh-execute` Step 1's existing gate only tests whether the target WI's
file exists on `origin/main`, and its stop message is free prose. Extend it
to also catch a WI that is present on `origin/main` but not
`status: proposed` because an open lifecycle PR (e.g. a reopen) will change
it, and give every such stop a fixed `Immediate next action / Why / After
that` report so the later `/lrh-execute` command cannot be mistaken for the
current action.

## Problem / Context

In an LCATS session, PR #463 reopened `WI-LINGUISTICS-0014` for
implementation. While that PR was still open, the assistant presented
`/lrh-execute WI-LINGUISTICS-0014` as "the next step" even though the real
immediate action was `/lrh-land <PR #463 URL>`. The later command appeared
as the primary actionable item.

Current behavior (`src/lrh/skills/lrh-execute/SKILL.md` Step 1,
`references/creation-pr-check.md`): the gate checks existence on
`origin/main` only. A WI that exists there but is waiting on an open
status-correcting PR passes that gate. For a direct `WI-ID`, Step 1 does
not check `status: proposed` on `origin/main` (the `WS-ID` path does), and
nothing looks for an open PR modifying the WI's file. The stop message that
does exist ("Land it first, then re-run `/lrh-execute`") has no structured
shape and no rule about how the later command is displayed.

### Prior Art Check

**Duplication search.** Ran `git grep -liE "open-prereq|open prerequisite"`
over `src/`, `project/design/proposals/`, `project/workstreams/`,
`project/work_items/`, `.claude/skills/`, `.agents/skills/`, excluding this
file: no matches.

**Demand search / related items.**
- `WI-EXECUTE-EARLY-CREATION-PR-CHECK` (resolved, PR #651) covers the
  file-absent case only, and has no test coverage. This WI extends it, not
  duplicates it.
- `WI-SKILLS-LRH-NEXT-STEP-REPORTING` (proposed) owns the shared cross-skill
  next-step reporting contract for `/lrh-work-item`, `/lrh-proposal`,
  `/lrh-workstream` and `/lrh-work-remains`. It requires its own decision
  matrix and does not cover `/lrh-execute`. This WI deliberately stays
  within `/lrh-execute` and uses a stop-report template that can be lifted
  into that shared contract later.

## Scope

- Extend the Step 1 gate (SKILL.md and `creation-pr-check.md`) to detect a
  target WI that is absent from `origin/main`, or present with a status
  other than `proposed`, together with an open PR that modifies the WI's
  exact file path (exact-path lookup via `gh pr list`, not a fuzzy search).
- Add a stop-report template: `Immediate next action: /lrh-land <PR>`,
  `Why`, `After that`. The later `/lrh-execute <WI-ID>` is shown only as
  inline prose marked non-actionable.
- Apply the same check per candidate for `WS-ID` targets: skip the
  ineligible candidate, continue in list order, and name the blocking PRs
  if no candidate is ready.
- Ensure no prompt ID is minted on a Step 1 stop and that the stop is
  recorded as `stopped` in the Step 5 run journal.
- Add a regression test and mirror the skill changes to `.claude/skills/`
  and `.agents/skills/` (and reinstall `.gemini` via the installer).

## Required Changes

1. Edit `src/lrh/skills/lrh-execute/SKILL.md` Step 1 and the Quality
   Checklist to cover the status-mismatch case and the structured stop
   report.
2. Edit `src/lrh/skills/lrh-execute/references/creation-pr-check.md` with
   the exact-path open-PR lookup, the zero-or-multiple-match generic
   fallback (no guessed PR), and the `WS-ID` skip behavior.
3. Add a regression test under `tests/` covering the open-prerequisite case
   for `WI-ID` and `WS-ID`, and mirror consistency across `src/`,
   `.claude/` and `.agents/`.
4. Mirror the skill files and reinstall `.gemini` through the installer.

## Non-Goals

- No shared cross-skill next-step contract; that belongs to
  `WI-SKILLS-LRH-NEXT-STEP-REPORTING`.
- No change to `/lrh-implement`, `/lrh-land`, or any chain-authorization,
  review, or merge gate.
- Does not auto-land the prerequisite PR.

## Acceptance Criteria

- A WI-ID with an open prerequisite PR stops at Step 1 with
  `Immediate next action: /lrh-land <PR>`, before any prompt minting.
- The later execution command is never in a standalone code block or
  labelled "next step".
- WS-ID resolution skips blocked candidates and reports blocking PRs if
  none is ready.
- A regression test covers both targets and mirror consistency.
- Existing valid flows and all human gates are unchanged.
- Canonical format, lint, tests and `lrh validate` pass.

## Validation

- scripts/format
- scripts/lint
- scripts/test
- lrh validate

## Risk Notes

- The skill is prose, so the regression test pins required text and
  structure; it cannot exercise runtime agent behavior.
- A file-path PR lookup can match unrelated PRs touching the same file. With
  zero or more than one open match the report stays generic and names no
  PR, as the existing creation-PR check already does.
