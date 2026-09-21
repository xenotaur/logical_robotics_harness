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
depends_on:
  - WI-LRH-CLOSEOUT-PR-VERIFIER
blocked_by: []
expected_actions:
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - weaken_human_gate
acceptance:
  - Step 7 lands closeout via a closeout PR by default (detached HEAD pushed to refs/heads/closeout-<slug>, merged only after the WI-LRH-CLOSEOUT-PR-VERIFIER command exits 0 for that PR and the head SHA it pushed is locked with --match-head-commit); a direct push to main happens only when the human's Step 2 answer explicitly names it
  - The Step 6 summary presents the closeout PR's concrete plan (allowed paths, the record fields to be written, the verification that will run, and the SHA-locked merge command shape with the head SHA pending), and one live in-session reply after that summary authorizes both merges; on any verifier divergence the agent asks again with the structured diff
  - A new decision, DEC-DERIVATIVE-PR-MERGE-PREAUTHORIZATION, amends DEC-AGENT-EXECUTED-MERGE-GATE in the way DEC-SINGLE-ASK-RUN-GATES amended DEC-DELIBERATE-CHAIN-INITIATION, and AGENTS.md's per-PR authorization line is edited to match, limited to closeout PRs
  - The decision states that authorization remains a live in-session reply after the Step 6 summary, that per-PR authorization for every other PR is unchanged, that required approvals on protected repos are still enforced by GitHub (the merge then falls back to the human), and that the verifier checks conformance to a human-authorized plan and is not an autopilot tier
  - A premature merge reply (one that arrives before the Step 6 summary is presented) is treated as non-authorizing; the summary is presented and the question is asked again (Step 6 marked region)
  - A records-only closeout PR is exempt from a fresh substitute review signal only when it touches nothing outside project/executions/**, project/work_items/**, project/workstreams/**, project/design/proposals/**, project/sessions/index.jsonl, and project/config/chain-defaults.yaml limited to its confirmed_commit and confirmed_at lines (the same set the verifier enforces)
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
  - project/memory/decisions/DEC-DERIVATIVE-PR-MERGE-PREAUTHORIZATION.md
  - AGENTS.md
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
`main`, with the closeout-PR merge covered by the Step 6 plan under a
mechanical conformance check rather than a second, separate ask. The scope
follows the assessment and decisions made in the session that created this
work item, revised after review of PR #684.

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
disagrees with Step 5. Note that PR #683 changed Step 7 again after this work
item was drafted; implementation must start from current `origin/main`.

**Review outcome on the closeout-PR authorization (PR #684, Codex P1).** A
review pointed out that the Step 6 reply is given before the closeout PR, its
head SHA and its SHA-locked command exist, and that `AGENTS.md:153` says
authorization is per-PR. Two designs were considered. A separate merge gate
after the closeout PR exists was rejected because it reintroduces the extra
ask that `DEC-SINGLE-ASK-RUN-GATES` deliberately removed. Instead, this work
item adopts a bounded pre-authorization: the Step 6 summary presents the
closeout PR's concrete plan, and the merge runs only if a mechanical verifier
(`WI-LRH-CLOSEOUT-PR-VERIFIER`) confirms the actual PR conforms to it, with the
head SHA locked. That requires a new decision because merge authorization is a
protected gate (`DEC-SINGLE-ASK-RUN-GATES` rule 5), and because
`DEC-AGENT-EXECUTED-MERGE-GATE` requires the exact SHA-locked command to be
presented before the merge. Protection on the base branch is a per-repo GitHub
setting: a `pull_request` rule with required approvals is still enforced by
GitHub and makes the merge fall back to the human; probing that is
`WI-LRH-BRANCH-PROTECTION-PROBE-AND-GUIDE`.

Prior art check:

- **Duplication:** none found. The resolved `WI-LAND-*` items cover other
  land defects, and PR #680 already replaced the tmp-branch flow with a
  detached HEAD.
- **Demand:** no existing work item, proposal or backlog entry requests
  closeout-PR landing; the only prior signal is a feedback memory that
  direct closeout pushes to `main` are blocked in auto mode and land via PR.

Marked `GATE-DEFINITION` regions in `SKILL.md`, `land-workflow.md` and
`chain-defaults.md` are watched by `lrh chain-defaults check-staleness`;
editing inside them invalidates users' stored skip-consent. PRs #680 and #683
already edited such regions, so the changes here add to that one re-grant.

## Scope

- Clarifications outside every marked region (Steps 1, 2, 4 and 5 wording,
  `confirm-fixes-workflow.md`, stale-text cleanups).
- Three approved gate-semantics changes inside marked regions: the
  premature-reply rule, the records-only closeout PR exemption, and
  closeout-PR landing as the Step 7 default with its Step 6 plan-preview
  authorization.
- The new decision and the matching `AGENTS.md` edit.
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
- Step 6 and Step 7 (marked): the Step 6 summary presents the closeout PR's
  concrete plan. Step 7 pushes a detached HEAD to `refs/heads/closeout-<slug>`,
  opens the closeout PR with `gh pr create --head closeout-<slug>`, runs the
  `WI-LRH-CLOSEOUT-PR-VERIFIER` command, and merges with
  `--match-head-commit <sha-it-pushed>` only on exit 0; any divergence asks
  again with the structured diff. A direct push to `main` happens only when
  the human's Step 2 answer explicitly names it. The Step 7 anti-pattern
  paragraph is reworded to match.
- Records-only closeout PR exemption: no fresh substitute review signal is
  required only when the PR touches nothing outside the enumerated set
  `project/executions/**`, `project/work_items/**`, `project/workstreams/**`,
  `project/design/proposals/**`, `project/sessions/index.jsonl`, and
  `project/config/chain-defaults.yaml` limited to its `confirmed_commit` and
  `confirmed_at` lines. This set must be identical to the verifier's allowed set.
- New decision `DEC-DERIVATIVE-PR-MERGE-PREAUTHORIZATION`: a bounded,
  human-authorized plan may cover the merge of a derivative PR that does not
  yet exist, when (1) the Step 6 summary presents that PR's concrete plan, (2)
  a mechanical verifier confirms conformance, (3) the head SHA is locked with
  `--match-head-commit`, and (4) the reply is live and in-session after the
  summary. Scope: closeout PRs only. Unchanged: `DEC-AGENT-EXECUTED-MERGE-GATE`'s
  reply classification, per-PR authorization for every other PR, and required
  approvals on protected repos, which GitHub enforces and which make the merge
  fall back to the human. The verifier is not an autopilot tier, consistent
  with `src/lrh/confirm_fixes_batch.py`'s statement that the merge gate is
  excluded from autopilot. Edit `AGENTS.md`'s per-PR authorization line to
  reference it.
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
- No autopilot or unattended merge tier.
- No change to the `permissions.deny` list or to the detached-HEAD flow beyond
  adapting it to the closeout PR.
- The verifier itself (`WI-LRH-CLOSEOUT-PR-VERIFIER`) and the branch-rules
  probe and how-to (`WI-LRH-BRANCH-PROTECTION-PROBE-AND-GUIDE`) are separate
  work items.

## Acceptance Criteria

- Step 7 lands closeout via a closeout PR by default, gated by the verifier
  and a head-SHA lock; a direct push to `main` only when named at Step 2.
- The Step 6 summary presents the closeout PR's concrete plan and one live
  reply after it authorizes both merges; divergence asks again.
- The new decision exists and the `AGENTS.md` line matches it.
- A premature merge reply is non-authorizing.
- The records-only exemption uses the enumerated path set above.
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
  (one re-grant per user); PRs #680 and #683 already triggered this.
- The new decision changes a protected gate's authorization model and needs
  the human's explicit approval of its wording at implementation time.
- Until the verifier exists, this work item cannot be implemented; it depends
  on `WI-LRH-CLOSEOUT-PR-VERIFIER`.
- The closeout-PR path adds one CI wait per land.
- The records-only exemption must stay narrow so it cannot become a way to
  skip review of real changes; its path set must stay identical to the
  verifier's.
- `.agents/` and `.gemini/` copies differ from the source in frontmatter;
  regenerate them with the installer rather than copying by hand.
