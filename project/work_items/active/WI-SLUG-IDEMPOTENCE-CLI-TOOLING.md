---
resolution: null
blocked_reason: null
blocked: false
id: WI-SLUG-IDEMPOTENCE-CLI-TOOLING
title: Build a CLI mechanism for pre-mint slug idempotence detection
type: deliverable
status: active
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-04
related_workstreams:
  - WS-EXECUTION-FRAMEWORK
related_design:
  - project/memory/decisions/DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT.md
  - PROMPTS.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - write_docs
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - change_prompts_md_invariant_or_default
  - fix_prompt_workflow_utc_timestamp_bug
acceptance:
  - a new lrh prompt check-execution --slug subcommand exists, matched to the complete trailing filename segment (not a bare substring), with unit tests covering local-checkout matches, cross-PR matches (including forks), stacked-PR merge-base inheritance, and force-pushed branches
  - the command fails loudly (non-zero exit, clear message) on gh/git fetch errors instead of silently reporting "no prior record"
  - lrh-proposal, lrh-work-item, and lrh-workstream call the new command instead of their inlined find/gh pr list/merge-base shell block
  - lrh-review-response and lrh-confirm-fixes call the same command, each keeping their own existing policy on the result (hard stop vs. Decision 12's warning-only re-verification)
  - both SKILL.md mirrors (src/lrh/skills and .claude/skills) are updated identically for every migrated skill, verified by diff -r
  - lrh validate passes with 0 errors and the full test suite passes
required_evidence:
  - code_diff
  - unit_tests
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/prompt_workflow.py
  - src/lrh/prompt_workflow_queries.py
  - tests/assist_tests/prompt_workflow_slug_test.py
  - src/lrh/skills/lrh-proposal/SKILL.md
  - .claude/skills/lrh-proposal/SKILL.md
  - src/lrh/skills/lrh-work-item/SKILL.md
  - .claude/skills/lrh-work-item/SKILL.md
  - src/lrh/skills/lrh-workstream/SKILL.md
  - .claude/skills/lrh-workstream/SKILL.md
  - src/lrh/skills/lrh-review-response/SKILL.md
  - .claude/skills/lrh-review-response/SKILL.md
  - src/lrh/skills/lrh-confirm-fixes/SKILL.md
  - .claude/skills/lrh-confirm-fixes/SKILL.md
---

# Build a CLI mechanism for pre-mint slug idempotence detection

## Summary

Replace the hand-rolled shell (`find` + `gh pr list` + `git merge-base` +
`created_at` comparison) currently duplicated across five skills with a
single tested CLI command, `lrh prompt check-execution --slug <slug>`,
that is the one place this logic lives and is verified.

## Problem / Context

`lrh prompt label` mints a fresh timestamped prompt ID on every call, so
the exact-ID lookup (`lrh prompt check-execution --prompt-id <id>`) cannot
by itself detect a rerun of the same logical slug before an ID exists to
look up. PRs #438, #440, and #441 (harness) built a filename-slug search to
cover this gap, promoted to policy in
`project/memory/decisions/DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT.md` as an
**invariant** (trailing-segment slug match is authoritative) plus a
**default** (block on `landed`/`in_progress`, continue on
`failed`/`reverted`/`superseded`). That decision record's own Alternative 3
and Revisit Conditions name this CLI as "the most complete long-term
answer," to be revisited once built.

Three concrete costs of the current shell-only mechanism, confirmed
directly against the repository:

- **Duplication.** The same block (derive `SLUG_UPPER_UNDERSCORE`,
  `find project/executions/AD_HOC/ -name "*_<SLUG>.md"`, cross-PR
  `gh pr list` + `git merge-base` fork/stacked-PR check, `created_at`
  recency comparison) is independently authored in
  `src/lrh/skills/lrh-work-item/SKILL.md:169-238`,
  `src/lrh/skills/lrh-proposal/SKILL.md`, and
  `src/lrh/skills/lrh-workstream/SKILL.md` — confirmed near-identical by
  direct diff. `src/lrh/skills/lrh-review-response/SKILL.md:122-131` and
  `src/lrh/skills/lrh-confirm-fixes/SKILL.md:177-187` carry their own,
  independently-evolved variants. This duplication already caused real
  drift once: the decision record's own Rationale notes
  `lrh-review-response` "never matched what PR #438/#440 described as
  'the applied pattern.'"
- **No test coverage.** `tests/assist_tests/` has dedicated test files for
  the CLI's other lookup mechanisms
  (`prompt_workflow_match_test.py` for exact-ID matching,
  `prompt_workflow_search_test.py` for exploratory search), but no
  equivalent exists for the shell-embedded slug search — because it is
  markdown prose, not Python, it is structurally outside the existing test
  suite. Every bug found across PRs #438/#440/#441's ~18 combined review
  rounds (fork detection, force-push staleness, a stacked-PR
  merge-base correctness bug, a local-time-vs-UTC filename chronology
  issue) was caught by manual review or ad hoc local git simulations, not
  by a repeatable regression test.
- **Existing scaffolding makes this cheaper than it looks.**
  `src/lrh/prompt_workflow.py:162-223` already defines the `argparse`
  subcommand pattern (`label`, `record-execution`, `check-execution`,
  `update-execution`); `prompt_workflow_match.py` and
  `prompt_workflow_search.py` are structurally adjacent siblings solving
  the same shape of problem (exact-ID match, exploratory search,
  respectively) with their own test files as a pattern to follow.

Prior-art check performed 2026-07-30:

- **Duplication search:** No existing work item covers building this CLI
  command. `grep -rl idempoten project/work_items/` returns no matches.
  The idea is tracked only as Alternative 3 in
  `DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT.md` and as the "Filename-slug
  idempotence search drives blocking, contrary to `PROMPTS.md`" entry in
  `project/design/backlog.md` (marked Resolved for the policy question;
  this work item is the "Not done — revisit if this resurfaces" follow-on
  it names). Verdict: no duplicate.
- **Demand search:** The decision record names this as one of its own
  three revisit conditions and the user confirmed wanting to pursue it
  after a step-by-step pros/cons analysis grounded in the current repo
  state (2026-07-30 session). Verdict: demand exists, previously
  uncaptured as a work item.

## Scope

Add a new `check-execution --slug` mode to the existing `lrh prompt`
CLI (`src/lrh/prompt_workflow.py` plus a query-layer module alongside
`prompt_workflow_match.py`/`prompt_workflow_search.py`), covering local
and cross-PR/fork detection, then migrate all five consuming skills to
call it. This work item **includes** fixing the fail-closed error-handling
gap (the shell version's `gh pr list`/`git fetch` calls suppress both
stderr and exit status, so a genuine API/network failure looks identical
to "no prior record") — implementing this in Python is a natural place to
do it correctly, and it closes the "Idempotence cross-PR discovery
doesn't fail closed on fetch errors" backlog entry as a side effect.

## Required Changes

- Add a query-layer module (parallel to `prompt_workflow_match.py`/
  `prompt_workflow_search.py`) implementing:
  - local `project/executions/<bucket>/` trailing-segment filename match
  - cross-PR discovery via `gh pr list` + `refs/pull/<N>/head` fetch
    (force-refspec, to handle force-pushed PRs)
  - stacked-PR inheritance detection via `git merge-base` against each
    PR's declared base ref (the PR #441 fix, ported from shell to Python)
  - recency ordering by each match's `created_at` frontmatter, not
    filename lexicographic order (sidesteps the still-open
    `prompt_workflow.py` UTC-timestamp bug rather than depending on it
    being fixed first)
  - explicit, loud failure (raised exception / non-zero exit + message)
    on any `gh`/`git` command failure, instead of the current silent
    "empty output = no match" behavior
- Wire a `--slug` (and `--work-item`/bucket) option into
  `check-execution` in `src/lrh/prompt_workflow.py:195-206`, returning
  structured results (matches with `execution_id`, `status`, `pr`, `path`)
  consumable by both a human-readable CLI report and by skill automation.
- Add `tests/assist_tests/prompt_workflow_slug_test.py` covering: no
  match, local match, cross-PR match, stacked-PR false-positive rejection,
  force-push staleness, and a simulated `gh`/`git` failure asserting the
  command fails loudly rather than reporting "no match."
- Migrate `lrh-proposal`, `lrh-work-item`, and `lrh-workstream` Step 4 to
  call the new command instead of inlining the shell block; each keeps its
  own block-on-`landed`/`in_progress` default behavior, now reading it
  from the command's output rather than re-deriving it.
- Migrate `lrh-review-response` Step 3 and `lrh-confirm-fixes` Step 3 to
  call the same command; each keeps its own existing policy on the result
  (`lrh-review-response`'s hard stop; `lrh-confirm-fixes`'s
  warning-only re-verification per Decision 12) — this work item changes
  the mechanism, not either skill's policy.
- Update every migrated skill's `src/lrh/skills/` and mirrored
  `.claude/skills/` copy identically.

## Non-Goals

- No change to `PROMPTS.md`'s invariant/default text itself — this work
  item implements the mechanism the decision record already describes; it
  does not revisit the policy.
- No fix to `src/lrh/prompt_workflow.py`'s local-time-vs-UTC filename
  timestamp bug (tracked separately in `project/design/backlog.md`,
  "Execution-record filename timestamps use local time, not UTC"). The
  new command sidesteps it via `created_at` comparison, the same
  workaround PR #441 already applied in shell; fixing the root cause is
  independent follow-up work, not a prerequisite.
- No changes to the `planned`-status gap the decision record explicitly
  left unresolved — still deferred to whichever skill first needs a
  concrete answer.
- No new interactive/AskUserQuestion flows beyond what each migrated
  skill already does today with a match.

## Acceptance Criteria

- `lrh prompt check-execution --slug <slug> --work-item <bucket>` exists,
  matches the complete trailing filename segment, and is covered by unit
  tests for: no match, local match, cross-PR match (including a fork),
  stacked-PR inheritance correctly excluded, force-push staleness handled,
  and a simulated fetch failure causing loud (non-silent) failure.
- `lrh-proposal`, `lrh-work-item`, `lrh-workstream`, `lrh-review-response`,
  and `lrh-confirm-fixes` all call the new command; no skill re-implements
  the find/merge-base/fetch logic inline any longer.
- Each migrated skill's block-vs-warn policy is unchanged from its
  current behavior (verified by re-reading each skill's decision logic
  before and after migration).
- `diff -r src/lrh/skills/<skill> .claude/skills/<skill>` exits 0 for
  every migrated skill.
- `lrh validate` reports 0 errors; full test suite (`pytest` /
  `scripts/test` or repo equivalent) passes.

## Validation

- `pytest tests/assist_tests/prompt_workflow_slug_test.py` (new) and the
  full existing `tests/assist_tests/` suite pass.
- `diff -r src/lrh/skills/lrh-proposal .claude/skills/lrh-proposal` (and
  the same for the other four migrated skills) exits 0.
- `lrh validate` reports 0 errors.
- Manual dogfood: run the migrated `/lrh-work-item` (or another migrated
  skill) idempotence check against a real open PR pair reproducing the
  PR #441 stacked-PR scenario, confirming the CLI correctly excludes the
  inherited match.

## Risk Notes

This is the third attempt at this exact problem (PR #438 introduced it,
PR #440 tried a universal `PROMPTS.md` matrix and hit structural
contradictions, PR #441 hardened the shell version through 6 review
rounds). Scope this as one bounded work item with the edge cases above
already enumerated as acceptance criteria and real unit tests as the
definition of done — the pattern that produced ~18 combined review rounds
across the prior three PRs was incremental, in-place hardening discovered
round-by-round rather than edge cases specified up front. Do not split
this into a "PR that grows via review" the way its predecessors did;
if new edge cases surface during implementation, prefer filing them as
follow-up backlog items over expanding this work item's scope mid-flight.
