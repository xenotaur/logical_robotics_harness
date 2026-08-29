---
resolution: null
blocked_reason: null
blocked: false
id: WI-EXECUTE-EARLY-CREATION-PR-CHECK
title: Stop /lrh-execute before chain authorization when the target WI's creation PR is still open
type: operation
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
  - modify_lrh_implement
acceptance:
  - "/lrh-execute Step 1, given a WI-ID, detects an open PR that would introduce that WI (not yet on origin/main) and stops with a clear \"land the introducing PR first\" message before Step 1.5/Step 2 run"
  - "For a WS-ID, a candidate WI whose creation PR is still open is skipped as ineligible and evaluation continues down the ordered work_items list, rather than aborting the whole run -- only a direct WI-ID input hard-stops"
  - "The matching logic is deliberately reused/adapted from /lrh-land's existing primary-record provenance-check algorithm rather than re-derived from scratch, with the execution record documenting which parts were reused vs. adapted"
  - "No change to /lrh-implement's own Step 5 check landed by the prior fix -- this is a strictly earlier, redundant check"
  - "lrh validate passes with 0 errors; existing /lrh-execute test/behavior coverage still passes"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/skills/lrh-execute/SKILL.md
  - src/lrh/skills/lrh-execute/references/
  - .claude/skills/lrh-execute/SKILL.md
  - .agents/skills/lrh-execute/SKILL.md
  - .gemini/plugins/lrh/skills/lrh-execute/SKILL.md
---

## Summary

Add a precondition check to `/lrh-execute` Step 1 that detects an open,
unmerged PR introducing the target WI and stops before any setup work or
the Step 2 chain-authorization gate -- rather than only being caught
downstream at `/lrh-implement` Step 5's just-landed re-check
([PR #602](https://github.com/xenotaur/logical_robotics_harness/pull/602)).

## Problem / Context

While landing `WI-PROJECT-SLUG-SYMLINK-RESOLUTION` (PR #603 planning, PR
#615 implementation) in a single session, `/lrh-execute` was invoked
against a WI-ID whose own creation PR (#603) was still open. `/lrh-execute`
Step 1's readiness check (`lrh work-items readiness <WI-ID>`) read the WI
file from the local working tree, which still had it (the session was
sitting on the WI-creation branch), and reported `prompt_ready: yes` with
no warnings -- a false-confidence result, since the file did not exist on
`origin/main` at all. This was only caught by manually running
`git status`/`gh pr view` outside any skill-enforced check.

`PR #602` has since landed a fix for the underlying silent-omission bug,
but it catches the problem at `/lrh-implement` Step 5 (right before
`git checkout -b <branch-name>`), which `/lrh-execute` Step 3 inlines. By
that point in an `/lrh-execute` run, the following has already happened:
Step 1's readiness check ran (and reported clean, since it reads the local
tree not `origin/main`), the prior-art check ran, the prompt ID was
minted, the idempotence check ran, the branch name was derived, and --
most significantly -- the Step 2 chain-authorization gate already fired
and the human already approved a full run plan (prompt_id, branch, task
summary, expected file changes, validation commands, readiness result,
prior-art result). Only then does Step 5 discover the WI isn't on `main`
and stop. This is safe (the bug is fully prevented) but wasteful: a run
that cannot possibly succeed still consumes a human confirmation cycle and
several mechanical setup steps before failing.

This is explicitly a UX/efficiency improvement, not a correctness fix --
`PR #602` already makes the underlying bug impossible to actually hit (it
always stops before any real work happens, just later than ideal).

### Duplication search
- In-repo: No existing fix. `git grep -i "creation.*pr.*early\|pre-mint.*creation-pr"`
  across `project/` returns no hits. `PR #602` fixed a related but distinct
  problem (the actual silent-omission bug, at a later point in the chain) --
  it does not duplicate this WI's earlier-stop scope.
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed.

### Demand search
- Work items: None found requesting this specific earlier-stop check.
- Proposals: None found.
- Backlog: A companion backlog entry is being added alongside this WI's
  creation (see `project/design/backlog.md`) to ensure this doesn't get
  lost; no pre-existing entry found before this WI.
- Recommendation: No action beyond the backlog entry accompanying this WI.

## Scope

- Add an earlier, redundant-but-faster-failing precondition check to
  `/lrh-execute` Step 1 (both the `WI-ID` and `WS-ID` branches)
- Reuse/adapt matching logic from `/lrh-land`'s existing primary-record
  provenance-check algorithm rather than re-deriving one from scratch

## Required Changes

1. In `src/lrh/skills/lrh-execute/SKILL.md` Step 1's `WI-ID` branch, add a
   check (alongside the existing `depends_on` enforcement) for an open,
   unmerged PR that would introduce the target WI-ID -- e.g. by searching
   execution records under `project/executions/AD_HOC/` for a record whose
   slug matches the WI and whose `pr:` field is still open, or by searching
   open PRs whose diff/body references the WI-ID. If found, stop and report
   "land PR #<N> first" before proceeding to Step 1.5/Step 2.
2. Apply the same check to Step 1's `WS-ID` branch, but **not** as a hard
   stop there: a candidate WI whose creation PR is still open is simply
   ineligible, the same as a candidate that fails `depends_on` or
   readiness today. Skip it and continue evaluating the ordered
   `work_items:` list for the next candidate, per `/lrh-execute`'s
   existing "next ready WI" selection rule (`PROP-LRH-LAND-EXECUTE`'s
   "Chosen scope") -- aborting the whole run on the first blocked
   candidate would incorrectly prevent selecting a later, fully-ready
   candidate. Only the direct `WI-ID` input case hard-stops, since there
   the human named that specific WI and no alternative candidate exists
   to fall back to.
3. Study `src/lrh/skills/lrh-land/references/land-workflow.md`'s "Primary
   vs. side-record provenance check" section before designing the matching
   logic here -- that section documents three prior failed attempts at a
   similar WI/slug-matching problem (bare filename-suffix exclusion, bare
   substring/trailing-exact globs, repo-wide base-slug lookups) before a
   working algorithm landed. Reuse or adapt its approach rather than
   re-deriving a new one from first principles.
4. Propagate the `SKILL.md` change to the `.claude/`, `.agents/`, and
   `.gemini/` mirrors via
   `lrh skills install --local --target all --source current-repo --force`.
5. Document in this WI's execution record which parts of the provenance-
   check algorithm were reused vs. adapted, and why.

## Non-Goals

- Do not re-derive `/lrh-land`'s primary-record provenance-check algorithm
  itself -- adapt/reuse it.
- Do not change anything in `/lrh-implement` -- `PR #602` already fixed the
  actual correctness bug there; this WI adds a strictly earlier, redundant
  check in `/lrh-execute` only.
- Do not attempt to make the check perfectly precise on every edge case in
  one pass -- per the Risk Notes below, expect at least one review round.

## Acceptance Criteria

- `/lrh-execute` Step 1, given a `WI-ID` directly, detects whether an open
  PR would introduce that WI and hard-stops with a clear message before
  Step 1.5/Step 2 run.
- For a `WS-ID`, a candidate WI whose creation PR is still open is skipped
  as ineligible (not a hard stop) and evaluation continues down the
  ordered `work_items:` list to the next candidate.
- The matching logic is documented as reused/adapted from `/lrh-land`'s
  provenance-check algorithm, not re-derived from scratch.
- No change to `/lrh-implement`'s own Step 5 check.
- `lrh validate` passes with 0 errors; existing `/lrh-execute` coverage
  still passes.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`

## Risk Notes

- This exact class of matching problem (PR/execution-record to WI/slug) has
  broken multiple times in this repo's own history before landing
  correctly -- bare filename-suffix exclusion, bare substring/trailing-exact
  globs, and repo-wide base-slug lookups have all been tried and reverted
  per `references/land-workflow.md`'s own account. Expect at least one
  review round to catch an edge case the first draft misses.
- A too-eager or falsely-positive check here (flagging a WI as blocked when
  it isn't) would itself introduce friction into every `/lrh-execute` run,
  the opposite of this WI's intent -- err toward "no confident match found,
  proceed" over "assume blocked" when the search is ambiguous, mirroring
  `/lrh-land`'s own "stop and ask, don't guess" precedent for ambiguous
  matches.
