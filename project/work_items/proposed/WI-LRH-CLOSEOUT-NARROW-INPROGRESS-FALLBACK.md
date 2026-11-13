---
id: WI-LRH-CLOSEOUT-NARROW-INPROGRESS-FALLBACK
title: Narrow /lrh-closeout's in_progress fallback to PR-relevant candidates
type: deliverable
status: proposed
blocked: false
blocked_reason: null
resolution: null
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design:
  - project/design/proposals/adopted/lrh-closeout/00_proposal.md
depends_on:
  - WI-LRH-CLOSEOUT-NO-EXECUTION-RECORD
blocked_by: []
expected_actions:
  - edit_file
  - create_file
forbidden_actions:
  - force_push
  - delete_branch
  - weaken_human_gate
  - edit_gate_definition_region
acceptance:
  - "When the quote-tolerant pr: search finds nothing, /lrh-closeout Step 2 lists only in_progress records that match the PR: execution_id containing the head branch's slug, work_item equal to a WI ID from the PR attribution scan (or listed by a WS ID it found), or a blank or placeholder pr: with created_at inside the PR's open-to-merge window"
  - "The PR attribution ID scan runs before the fallback on every invocation route, so the fallback can use it; the existing direct-invocation attribution step reuses the same IDs"
  - "An empty narrowed list goes straight to the No execution record branch, and the user can still ask for the full in_progress list at that point"
  - "references/closeout-workflow.md's decision matrix and its Creating a record when none exists section describe the narrowed fallback and the empty-list route"
  - "Step 5's new-record path runs the pre-mint check-execution --slug <slug> --work-item <bucket> check before lrh prompt label, per DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT, with exit-code handling"
  - "No GATE-DEFINITION region is edited"
  - "The installed .claude/skills/lrh-closeout and plugins/lrh/skills/lrh-closeout copies match src/lrh/skills/lrh-closeout"
  - "scripts/test, scripts/lint, scripts/format --check --diff and lrh validate are all clean"
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - project/work_items/proposed/WI-LRH-CLOSEOUT-NARROW-INPROGRESS-FALLBACK.md
  - src/lrh/skills/lrh-closeout/SKILL.md
  - src/lrh/skills/lrh-closeout/references/closeout-workflow.md
  - .claude/skills/lrh-closeout/SKILL.md
  - .claude/skills/lrh-closeout/references/closeout-workflow.md
  - plugins/lrh/skills/lrh-closeout/SKILL.md
  - plugins/lrh/skills/lrh-closeout/references/closeout-workflow.md
---

## Summary

Make `/lrh-closeout` Step 2's fallback, used when no execution record names
the PR in `pr:`, offer a short list of records that plausibly belong to the
PR instead of every `in_progress` record in the repository. When that list
is empty, go straight to the "No execution record" branch added by
`WI-LRH-CLOSEOUT-NO-EXECUTION-RECORD`.

## Problem / Context

PR #872 gave `/lrh-closeout` a path for a merged PR with no execution
record. That path fires only after the quote-tolerant `pr:` search finds
nothing and the `in_progress` fallback is empty or every candidate is
rejected. The fallback lists all `status: in_progress` records, and this
repo has 213 of them (`git grep -l '^status: in_progress' --
project/executions/ | wc -l`). In practice, the user has to reject 213
records to reach the new branch.

The PR-mode substitute self-review of PR #872
(`project/executions/AD_HOC/2026_11_13_03_00_07_WI_LRH_CLOSEOUT_NO_EXECUTION_RECORD_SELFREVIEW.md`)
recorded this as finding 1. Its finding 2 notes that Step 5 checks a freshly
minted prompt ID with `check-execution --prompt-id`, which can never find a
prior run, while other skills (`/lrh-execute`, `/lrh-proposal`,
`/lrh-work-item`) first run the pre-mint
`check-execution --slug <slug> --work-item <bucket>` check
(`DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT`).

Checked against PR #872's own records (as they stood before its closeout):
its head branch slug `wi-lrh-closeout-no-execution-record` appears in all
four of its execution IDs, including the diff-mode self-review record
created before the PR opened, and in none of the other 209.

Prior art check:

- **Duplication:** no existing skill narrows the fallback. `/lrh-closeout`
  Step 1's auto-detect has its own `in_progress` listing for choosing a
  target; that is a different question (which PR to close out) and is out
  of scope.
- **Demand:** the self-review record above names this as a follow-up work
  item. No other work item or backlog entry covers it.

## Scope

- Skill text only: `src/lrh/skills/lrh-closeout/SKILL.md` Steps 2 and 5,
  and `references/closeout-workflow.md`, plus their regenerated installed
  (`.claude/skills/`) and plugin (`plugins/lrh/skills/`) copies.

## Required Changes

- Step 2: move the PR attribution ID scan ahead of the fallback so every
  invocation route has it; filter `in_progress` records by head-branch
  slug, `work_item`, and blank-`pr:` creation window; send an empty result
  to the "No execution record" branch with an offer of the full list.
- Step 5: add the pre-mint slug check before `lrh prompt label` in the
  new-record path.
- `references/closeout-workflow.md`: update the decision-matrix rows and the
  "Creating a record when none exists" section and commands to match.

## Non-Goals

- No CLI change.
- No change to Step 1's auto-detect listing.
- No change to the Step 4 gate (a `GATE-DEFINITION` region).
- No change to how the `pr:` search matches non-URL values such as
  `owner/repo#N` (self-review finding 3).

## Acceptance Criteria

- All items in the `acceptance:` frontmatter list.

## Validation

- scripts/test
- scripts/lint
- scripts/format --check --diff
- lrh validate
- diff -r src/lrh/skills/lrh-closeout .claude/skills/lrh-closeout
- diff -r src/lrh/skills/lrh-closeout plugins/lrh/skills/lrh-closeout

## Risk Notes

- Narrowing can hide a real record whose branch, work item, and timing all
  fail to match (for example, a record created long before the PR on a
  differently named branch). The user can still ask for the full list, and
  Step 4's gate shows the planned new record before anything is written.
