---
resolution: 'Implemented and merged in PR #872 (commit 416843d5)'
blocked_reason: null
blocked: false
id: WI-LRH-CLOSEOUT-NO-EXECUTION-RECORD
title: Give /lrh-closeout a documented path for a merged PR with no execution record
type: deliverable
status: resolved
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design:
  - project/design/proposals/adopted/lrh-closeout/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - create_file
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - weaken_human_gate
acceptance:
  - /lrh-closeout Steps 1 and 2 name an explicit no-execution-record branch that fires only after both the pr-field search and the in_progress fallback come back empty (or the user rejects every fallback candidate)
  - Before defaulting to AD_HOC, the skill scans the PR title, body, head branch and commit messages for WI and WS IDs that exist in project/ and asks the user which work item, if any, the new record belongs to
  - The Step 2 plan table shows the missing record as its own row stating the bucket and that the record is created directly as landed
  - The Step 4 confirm gate shows the creation-time fields (work-item bucket, slug, agent, instruction_source, session_transcript) for the record to be created
  - Step 5 mints a prompt ID with lrh prompt label, checks it with lrh prompt check-execution, and creates the record with one lrh prompt record-execution --status landed call; it never calls lrh prompt update-execution for this record
  - When the closeout workflow runs inline from /lrh-land, the new branch defers to /lrh-land's no-primary backfill path and never creates a second record
  - references/closeout-workflow.md's decision matrix documents the new branch in its existing table style and replaces the bare "Missing entirely" row
  - The installed .claude/skills/lrh-closeout copy matches src/lrh/skills/lrh-closeout
  - scripts/test, scripts/lint, scripts/format --check --diff and lrh validate are all clean
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-closeout/SKILL.md
  - src/lrh/skills/lrh-closeout/references/closeout-workflow.md
  - .claude/skills/lrh-closeout/SKILL.md
  - .claude/skills/lrh-closeout/references/closeout-workflow.md
---

## Summary

Add a documented `/lrh-closeout` path for a merged PR that has no execution
record at all, so a closeout session creates the record directly as `landed`
instead of improvising the steps each time.

## Problem / Context

`/lrh-closeout` assumes at least one execution record exists for the target
PR. Step 1's auto-detect and Step 2's PR-URL path both fall back to listing
`in_progress` records when none matches by `pr:`, but neither says what to do
when that fallback is empty too. The decision matrix's only guidance is
"Missing entirely: warn user; ask whether to proceed without it".

That case is routine: a fix small enough to go from edit to commit to PR to
merge without `/lrh-implement` never gets a record, because `/lrh-implement`
Step 9 is what creates one. On 2026-11-07, closing out xenotaur/prosoc PR #139
(a one-line wording fix) hit exactly this. Both searches came back empty, and
the session improvised: it minted a prompt ID in the `AD_HOC` bucket and called
`lrh prompt record-execution --status landed` with `pr`, `commit`, `agent`,
`instruction_source` and `session_transcript` in one call, then wrote the
record body after the fact. That one-call creation works; `lrh prompt
update-execution` cannot be used because it only moves an existing
`in_progress` record to `landed`.

A PR that skipped `/lrh-implement` can still correspond to a real proposed
work item, so defaulting straight to `AD_HOC` could leave that work item
unresolved.

Prior art check:

- **Duplication:** `/lrh-land` Step 7 already has a "no-primary backfill"
  path that creates an `AD_HOC` record (as `in_progress`) before inlining the
  closeout workflow. It covers only the `/lrh-land` chain; direct
  `/lrh-closeout` has nothing. The new branch must defer to that path when
  inlined so a PR never gets two records.
- **Demand:** no existing work item or proposal requests this.
  `PROP-LRH-CLOSEOUT`'s decision matrix says only "missing: warn and ask".

## Scope

- Skill text only: `src/lrh/skills/lrh-closeout/SKILL.md` and
  `references/closeout-workflow.md`, plus their installed `.claude/skills/`
  copies.

## Required Changes

- Steps 1 and 2: add the no-execution-record branch, the WI/WS attribution
  scan, and the plan-table row.
- Step 3: resolve the session pointer for the record to be created, keyed on
  the confirmed agent.
- Step 4: show the creation-time fields and the attribution question at the
  gate.
- Step 5: label, check-execution, one `record-execution --status landed`
  call, then write the record body.
- Decision matrix: replace the "Missing entirely" row and add a short
  creation protocol section.

## Non-Goals

- No CLI change; `lrh prompt record-execution` already supports
  `--status landed` with all needed fields.
- No change to `/lrh-land`'s backfill path.
- No automatic WI attribution; the user always decides at Step 4.

## Acceptance Criteria

- All items in the `acceptance:` frontmatter list.

## Validation

- scripts/test
- scripts/lint
- scripts/format --check --diff
- lrh validate
- diff -r src/lrh/skills/lrh-closeout .claude/skills/lrh-closeout

## Risk Notes

- Step 4's confirm gate is inside a `GATE-DEFINITION` region, so this change
  marks the chain-defaults gates stale; re-confirm them with
  `/lrh-config-gates` after merge.
