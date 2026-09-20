---
resolution: null
blocked_reason: null
blocked: false
id: WI-LRH-LAND-WORDING-AND-CLOSEOUT-PR
title: Clarify /lrh-land wording and land closeout via a closeout PR
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
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - weaken_human_gate
acceptance:
  - Step 7 lands closeout via a closeout PR by default (detached HEAD pushed to refs/heads/closeout-<slug>, merged after CI is green and mergeable is clean); a direct push to main happens only when the human's Step 2 answer explicitly names it; Step 2 and the Step 6 summary name the closeout-PR merge so the single ask covers it
  - Merge authorization stays a live in-session reply given after the Step 6 summary; a premature merge reply is treated as non-authorizing and the summary is presented and re-asked (Step 6 marked region)
  - A records-only closeout PR is exempt from a fresh substitute review signal only when it touches nothing outside project/executions/, project/work_items/ and the closeout's own control-plane files
  - confirm-fixes-workflow.md and land Steps 5 and 6 check mergeable before treating "no checks reported" as CI silence, and a CONFLICTING PR is a stop-and-report
  - The clarification items from the assessment (Step 1 ambiguous prompt, Step 2 re-stamp placement note, Step 4 review-response ordering callout, Step 5 _SELFREVIEW record placement, one general compound-command sentence) and the stale-text cleanups are applied
  - lrh-closeout/SKILL.md lines that say closeout commits go directly to main and forbid a PR are amended outside its marked region
  - .claude/skills mirrors are byte-identical to src/lrh/skills; .agents/skills and .gemini/plugins/lrh/skills are regenerated via lrh skills install
  - lrh chain-defaults check-staleness output is reported, and scripts/test, scripts/lint, scripts/format --check --diff and lrh validate are all clean
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/skills/lrh-land/SKILL.md
  - src/lrh/skills/lrh-land/references/land-workflow.md
  - src/lrh/skills/lrh-confirm-fixes/references/confirm-fixes-workflow.md
  - src/lrh/skills/lrh-closeout/SKILL.md
  - .claude/skills/lrh-land/
  - .claude/skills/lrh-confirm-fixes/
  - .claude/skills/lrh-closeout/
  - .agents/skills/
  - .gemini/plugins/lrh/skills/
---

## Summary

Improve the wording of the `/lrh-land` skill and its shared references based
on friction hit while landing PRs #670 and #676, and change Step 7 so the
closeout lands through a small closeout PR instead of a direct push to
`main`. The scope follows the assessment and decisions made in the session
that created this work item.

## Problem / Context

Landing PRs #670 and #676 hit eight concrete friction points, assessed as
real defects, wording gaps or working-as-designed:

1. Step 7 assumes a direct `git push origin HEAD:main`; auto mode denied it
   as a "CI Bypass", and the closeout only landed via small closeout PRs
   (#675, #679).
2. The chain-defaults re-stamp has no stated location when `/lrh-land` runs
   from the PR's own branch, so doing it there pollutes the PR diff.
3. A "merge it" reply can arrive before the Step 6 summary; the skill does
   not say what to do with it.
4. Inlined review-response loses its ordering (mint prompt ID and present
   the confirm gate before any edit).
5. Records-only commits (`_CONFIRM`, `_SELFREVIEW`) change the PR head and
   cause a review-signal regress; the skill does not say where the
   `_SELFREVIEW` record goes or when a records-only head is exempt.
6. Chaining a deny-listed command with other commands denies the whole call.
   PR #680 already removed the `tmp-*` branch cleanup, so only one short
   general sentence remains in scope.
7. A CONFLICTING PR reports "no checks reported", which reads as slow CI.
   No `mergeable` check exists in `lrh-confirm-fixes` or `/lrh-land`.
8. Step 1's primary-record classification is ambiguous by naming alone once
   `_REVIEW`/`_CONFIRM`/`_SELFREVIEW` records exist for an ad hoc PR.

Reading the skill end to end also found stale text: a "Step 3" prompt-id
reference in the backfill snippet, contradictory interim-versus-permanent
invocation paragraphs in `land-workflow.md`, an "all worktrees" versus
"another worktree" trigger mismatch, leftover `tmp_branch_parent` and
"branch creation" wording after PR #680, and a checklist ordering that
disagrees with Step 5.

Prior art check:

- **Duplication:** none found. The resolved `WI-LAND-*` items cover other
  land defects, and PR #680 already replaced the tmp-branch flow with a
  detached HEAD.
- **Demand:** no existing work item, proposal or backlog entry requests
  closeout-PR landing; the only prior signal is a feedback memory that
  direct closeout pushes to `main` are blocked in auto mode and land via PR.

Marked `GATE-DEFINITION` regions in `SKILL.md`, `land-workflow.md` and
`chain-defaults.md` are watched by `lrh chain-defaults check-staleness`;
editing inside them invalidates users' stored skip-consent. PR #680 already
edited one such region, so the changes here add to that one re-grant.

## Scope

- Clarifications outside every marked region (Steps 1, 2, 4 and 5 wording,
  `confirm-fixes-workflow.md`, stale-text cleanups).
- Three approved gate-semantics changes inside marked regions: the
  premature-reply rule, the records-only closeout PR exemption, and
  closeout-PR landing as the Step 7 default.
- The `lrh-closeout/SKILL.md` amendment needed by closeout-PR landing,
  outside its marked region.
- Mirror sync and regeneration of the installed copies.

## Required Changes

Clarifications (unmarked):

- Add a `mergeable`/`mergeStateStatus` check in `confirm-fixes-workflow.md`
  ahead of the CI wait, with pointers from `/lrh-land` Step 5 and the Step 6
  merge-state verify; a CONFLICTING PR is stop-and-report.
- Add an ordering callout to Step 4: mint the prompt ID and present the
  confirm gate before any edit, even for a trivial-looking fix.
- Add a re-stamp placement note to Step 2: defer the chain-defaults re-stamp
  to the closeout commit, and note that re-stamping changes the file's blob
  hash and so invalidates stored skip-consent.
- Say where the `_SELFREVIEW` record is authored, and what to show the human
  when Step 1 reports an ambiguous primary record; state that Step 1's
  result carries into Step 7 and is not recomputed.
- Add one general sentence that deny-listed commands must never be placed in
  a compound call.
- Fix the stale text: backfill snippet prompt-id source, the interim versus
  permanent invocation contradiction, the "all worktrees" trigger, leftover
  `tmp_branch_parent` and "branch creation" wording, and the checklist
  ordering.

Gate-semantics changes (flag every touch of a marked region):

- Step 6 (marked): a merge reply that arrives before the summary is not
  authorization; present the summary and ask again.
- Step 7 (marked) and Steps 2 and 6: closeout lands via a closeout PR by
  default, from a detached HEAD pushed to `refs/heads/closeout-<slug>` with
  `gh pr create --head closeout-<slug>`, merged after CI is green and
  `mergeable` is clean. Step 2 and the Step 6 summary name that merge so the
  single ask covers it. A direct push to `main` happens only when the
  human's Step 2 answer explicitly names it. The Step 7 anti-pattern
  paragraph is reworded to match.
- Records-only closeout PR exemption: no fresh substitute review signal is
  required only when the PR touches nothing outside `project/executions/`,
  `project/work_items/` and the closeout's own control-plane files.
- `lrh-closeout/SKILL.md` lines 485, 539 and 560 are amended outside the
  marked region 273-307 so they no longer forbid a PR.

Sync:

- Copy the result to `.claude/skills/` byte-for-byte; regenerate
  `.agents/skills/` and `.gemini/plugins/lrh/skills/` with
  `lrh skills install`.

## Non-Goals

- No new chain-defaults or agent-config field (no `closeout_landing:` option).
- No change to the primary-record provenance algorithm.
- No relaxation of any human gate; merge authorization stays a live
  in-session reply after the Step 6 summary.
- No change to the `permissions.deny` list or to PR #680's detached-HEAD
  flow beyond adapting it to the closeout PR.

## Acceptance Criteria

- Step 7 lands closeout via a closeout PR by default; a direct push to
  `main` only when the human's Step 2 answer explicitly names it.
- Step 2 and the Step 6 summary name the closeout-PR merge.
- A premature merge reply is non-authorizing; authorization is a live reply
  after the summary.
- The records-only exemption is narrow, as specified above.
- `mergeable` is checked before "no checks reported" is read as CI silence.
- Clarification items and stale-text cleanups are applied.
- `lrh-closeout/SKILL.md` no longer forbids a PR.
- Mirrors are in sync and `check-staleness` output is reported.
- All validation commands below are clean.

## Validation

- scripts/test
- scripts/lint
- scripts/format --check --diff
- lrh validate
- lrh chain-defaults check-staleness --confirmed-commit <confirmed_commit> --project-root .
- diff -r src/lrh/skills/lrh-land .claude/skills/lrh-land
- diff -r src/lrh/skills/lrh-confirm-fixes .claude/skills/lrh-confirm-fixes
- diff -r src/lrh/skills/lrh-closeout .claude/skills/lrh-closeout

## Risk Notes

- Editing marked regions invalidates stored `skip_if_opted_in` consent
  (one re-grant per user); PR #680 already triggered this once.
- The closeout-PR path adds one CI wait per land, and its merge must be
  named in the Step 6 summary so the single ask stays honest.
- The records-only exemption must stay narrow so it cannot become a way to
  skip review of real changes.
- `.agents/` and `.gemini/` copies differ from the source in frontmatter;
  regenerate them with the installer rather than copying by hand.
