---
resolution: 'Implemented and merged in PR #467 (commit cdd1134)'
blocked_reason: null
blocked: false
id: WI-SKILLS-LRH-SELF-REVIEW
title: Implement /lrh-self-review Claude Code skill
type: deliverable
status: resolved
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams: []
related_design:
  - project/design/proposals/adopted/lrh-self-review/00_proposal.md
  - project/design/backlog.md
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
acceptance:
  - 'src/lrh/skills/lrh-self-review/SKILL.md exists with valid frontmatter (disable-model-invocation: true, --pr argument)'
  - src/lrh/skills/lrh-self-review/references/self-review-workflow.md exists
  - diff -r src/lrh/skills/lrh-self-review/ .claude/skills/lrh-self-review/ reports no differences
  - CLAUDE.md lists /lrh-self-review in the Skills section
  - /lrh-implement gains a Step 7.5 (diff-mode dispatch) before Step 8's gh pr create, in both skill trees
  - round-cap-gate.md documents self-review substitution as the three-way gate's fourth answer, and the post-ceiling PR-mode call path, in both skill trees
  - PROP-LRH-LAND-EXECUTE Decision 8's CHAIN-NOTE convention gains self_review_rounds= and bot_rounds= fields, with bot_rounds computed as completed_count minus self_review_rounds (not read directly from completed_count)
  - Primary-record/rerun_of exclusion globs in /lrh-review-response, /lrh-confirm-fixes, and /lrh-land also exclude _SELFREVIEW.md, in both skill trees
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-self-review/SKILL.md
  - src/lrh/skills/lrh-self-review/references/self-review-workflow.md
  - .claude/skills/lrh-self-review/SKILL.md
  - .claude/skills/lrh-self-review/references/self-review-workflow.md
  - CLAUDE.md
  - src/lrh/skills/lrh-implement/SKILL.md
  - src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md
---

# Implement `/lrh-self-review` Claude Code skill

## Summary

Implement the `/lrh-self-review` skill as designed in `PROP-LRH-SELF-REVIEW`:
a Claude Code skill that dispatches a cold-context subagent to independently
review a diff (before a PR's first push) or a PR (as a round-cap-gate
ceiling substitute), reducing dependence on metered GitHub bot-review
credits without altering the ceiling mechanism's own semantics.

## Problem / Context

Sessions landing PRs in this repo have been substituting ad hoc, hand-dispatched
subagent reviews for GitHub bot retriggers throughout the session, successfully — but
purely as free-text instructions interpreted per-invocation, with no packaged
skill, no execution-record trail distinguishing self-review from bot review,
and no formal path into `round-cap-gate.md`'s three-way gate. `PROP-LRH-SELF-REVIEW`
(`project/design/proposals/adopted/lrh-self-review/00_proposal.md`, merged
via PR #462) captures the full design: two trigger points (a single pre-push
diff-mode pass, and a post-ceiling PR-mode substitute as the gate's fourth
answer), why the pre-push pass is exempt from the ceiling by construction,
record-occurrence-not-currency tracking, and why a PR's first real bot round
is never skippable. `WI-REVIEW-LANDED-CANONICAL-CHECK` (proposed) already
excludes this exact capability from its own scope, naming it "a separate,
not-yet-filed future work item" — this item is that deferral, now filed.

### Duplication search
- In-repo: No existing implementation found — only a hypothetical mention in
  `lrh-confirm-fixes/SKILL.md:419-438` and an ad hoc `Agent`-dispatch pattern
  used by hand in PRs #447, #452, #457, #459, #460, #461, #462.
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed.

### Demand search
- Work items: Found: `WI-REVIEW-LANDED-CANONICAL-CHECK` (proposed) — defers
  this exact capability as future work.
- Proposals: Found: `PROP-LRH-SELF-REVIEW` — the governing design this item
  implements.
- Backlog: Found: "Self-review-first tier for reducing GitHub bot-review
  credit consumption" (`project/design/backlog.md`) — the evidence base.
- Recommendation: No action — this item is the demand these already name.

## Scope

- Implement `/lrh-self-review`: diff-mode and PR-mode, one skill,
  argument-driven (`--pr <url>`, default local diff)
- Wire diff-mode into `/lrh-implement` as a new Step 7.5
- Wire PR-mode into `round-cap-gate.md` as the three-way gate's fourth answer
- Add `self_review_rounds=`/`bot_rounds=` to the CHAIN-NOTE convention
- Add `_SELFREVIEW.md` to the primary-record/`rerun_of` exclusion globs in
  `/lrh-review-response`, `/lrh-confirm-fixes`, and `/lrh-land`, following
  the exact precedent set when `_CONFIRM.md` was introduced
- Mirror every change to `.claude/skills/`

## Required Changes

1. Create `src/lrh/skills/lrh-self-review/SKILL.md` (`disable-model-invocation: true`,
   `--pr` argument) — dispatch a `general-purpose` `Agent` subagent, cold
   context, verify claims against real files, independently re-verify its
   own top finding before accepting it (mandatory step per Decision 6),
   write an execution record (`AD_HOC`, `_SELFREVIEW` suffix).
2. Create `src/lrh/skills/lrh-self-review/references/self-review-workflow.md`
   — the shared procedure both modes use, the diff-mode vs. PR-mode prompt
   shapes, and the execution-record convention.
3. Mirror both to `.claude/skills/lrh-self-review/`.
4. Add a `/lrh-self-review` entry to `CLAUDE.md`'s `## Skills` index.
5. Add Step 7.5 to `src/lrh/skills/lrh-implement/SKILL.md` (+ mirror),
   between Step 7 (Validate) and Step 8 (Commit and PR) — diff-mode dispatch,
   apply fixes if any, then proceed to Step 8 regardless of findings
   (Decision 4: never skip the first real bot round).
6. Add the fourth three-way-gate answer to `round-cap-gate.md` (+ mirror):
   "substitute self-review for this round" — dispatches PR-mode instead of
   a bot retrigger; on completion, increments `completed_count` within the
   existing ceiling, same as a bot round (Decision 2's "Gate integration").
7. Add `self_review_rounds=`/`bot_rounds=` to the CHAIN-NOTE convention
   (currently defined in `PROP-LRH-LAND-EXECUTE` Decision 8) — this WI
   decides the concrete edit: a new amendment paragraph in that proposal,
   not a canonical-doc rewrite, since the proposal is still `status: proposed`
   itself. **`bot_rounds` must be computed as `completed_count -
   self_review_rounds`, not read directly from `completed_count`** —
   `PROP-LRH-SELF-REVIEW` Decision 2 has every PR-mode round (bot- or
   self-review-triggered) increment the same source-agnostic
   `completed_count`, so reading `bot_rounds` straight from that counter
   double-counts self-review rounds as if they were bot rounds too (e.g.
   1 bot round + 1 self-review round would report `bot_rounds=2`, not 1).
   `PROP-LRH-SELF-REVIEW`'s own Decision 3 text has this same imprecision
   and needs the matching correction — file it as a small amendment to
   that proposal alongside this WI's implementation, don't silently diverge
   from the governing design without updating it.
8. Update the `rerun_of`/primary-record exclusion globs in
   `src/lrh/skills/lrh-review-response/SKILL.md`,
   `src/lrh/skills/lrh-confirm-fixes/SKILL.md`, and
   `src/lrh/skills/lrh-land/SKILL.md` (+ all three `.claude/` mirrors) to
   also exclude `_SELFREVIEW.md` — mechanical addition to the existing
   pattern, not a redesign of it (see Risk Notes for the pre-existing,
   out-of-scope collision this does not fix).

## Non-Goals

- Does not implement diff-mode beyond `/lrh-implement`'s Step 7.5, or
  PR-mode beyond `/lrh-land`'s post-ceiling substitution — expansion to
  `/lrh-work-item`, `/lrh-proposal`, `/lrh-workstream`, `/lrh-doc-work`,
  etc. is explicitly deferred (proposal Non-Goals).
- Does not add a third "review approach" question to `/lrh-land`'s or
  `/lrh-execute`'s Step 2 chain-authorization gate (GitHub-bot-first /
  self-review-first / judgment-call) — genuinely useful, but depends on
  this WI landing first so the option is actionable. File as its own small
  follow-up WI once `/lrh-self-review` exists, not bundled here.
- Does not fix the general primary-record slug/suffix-collision gap (a
  topic slug ending in "review" or "confirm" self-excludes from
  `/lrh-land` Step 1's primary-record search) — pre-existing, not
  introduced by this WI's own `_SELFREVIEW.md` addition (see Risk Notes).
  File a separate backlog entry for the general fix.
- Does not create `WS-SKILLS-SELF-REVIEW` — offered as a separate
  follow-on via `/lrh-workstream`, not bundled into this WI's file-writing
  scope.
- Does not change `round-cap-gate.md`'s ceiling values, default suggestion
  sequence, or ask-the-human escalation flow itself — only adds the fourth
  answer.
- Does not measure or report actual GitHub AI-credit cost in currency or
  credit-unit terms (proposal Decision 3/Non-Goals).

## Risk Notes

- **Known, documented, pre-existing name-collision risk, not this WI's to
  fix.** `src/lrh/skills/lrh-review-response/SKILL.md:156-170` already
  documents that side-record filenames must end in the literal suffix the
  exclusion greps match (`_REVIEW.md`, `_CONFIRM.md`) — a deliberate
  convention, not sloppy behavior. But a *primary* record whose own topic
  slug happens to end in one of those same words self-excludes from
  `/lrh-land` Step 1's search. Verified live this session: `PROP-LRH-SELF-REVIEW`'s
  own creation record (`LRH_SELF_REVIEW.md`) tripped exactly this
  collision against the *existing* `_REVIEW.md` exclusion — unrelated to
  the `_SELFREVIEW.md` suffix this WI adds. Expect this to recur for future
  review-topic-named work; don't attempt the general fix here (see
  Non-Goals). Captured in agent memory as
  `feedback_lrh_land_step1_primary_record_substring_exclusion`.
- `round-cap-gate.md`'s state schema went through 8 review rounds to
  harden (documented in its own history) — scope the fourth-gate-answer
  addition narrowly to avoid re-opening that hardening.
- Bundling one new skill + three skills' exclusion-glob updates +
  `round-cap-gate.md` changes + a `PROP-LRH-LAND-EXECUTE` amendment into
  one PR is a wide surface, matching `WI-SKILLS-LRH-CONFIRM-FIXES`'s
  precedent shape — but that precedent needed a recovery PR (#398) after a
  merge race dropped review fixes from #397. Watch for the same risk here.

## Acceptance Criteria

- `src/lrh/skills/lrh-self-review/SKILL.md` and
  `references/self-review-workflow.md` exist with valid frontmatter.
- `diff -r src/lrh/skills/lrh-self-review/ .claude/skills/lrh-self-review/`
  reports no differences.
- `CLAUDE.md` lists `/lrh-self-review` in the Skills section.
- `/lrh-implement` has a Step 7.5 (both skill trees).
- `round-cap-gate.md` documents the fourth gate answer and PR-mode call
  path (both skill trees).
- `PROP-LRH-LAND-EXECUTE` Decision 8's CHAIN-NOTE convention gains
  `self_review_rounds=`/`bot_rounds=`, with `bot_rounds` computed as
  `completed_count - self_review_rounds`.
- `/lrh-review-response`, `/lrh-confirm-fixes`, `/lrh-land` exclusion globs
  also exclude `_SELFREVIEW.md` (both skill trees, all three).
- `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `diff -r src/lrh/skills/lrh-self-review/ .claude/skills/lrh-self-review/`
- `diff -r src/lrh/skills/lrh-implement/ .claude/skills/lrh-implement/`
- `diff -r src/lrh/skills/lrh-confirm-fixes/ .claude/skills/lrh-confirm-fixes/`
- `diff -r src/lrh/skills/lrh-review-response/ .claude/skills/lrh-review-response/`
- `diff -r src/lrh/skills/lrh-land/ .claude/skills/lrh-land/`

## Dependencies / Order

No hard `depends_on` — `PROP-LRH-SELF-REVIEW` is `status: proposed` (not
formally adopted) at filing time, matching the precedent of
`WI-SKILLS-LRH-CONFIRM-FIXES`, filed and implemented against a still-proposed
governing proposal (verified: `PROP-LRH-CONFIRM-FIXES`'s own Implementation
Plan used the identical "Depends on: This proposal adopted" phrasing, and
that WI also shipped with no hard `depends_on`). **This is a real, unresolved
tension, not a settled question** — the governing proposal's own
Implementation Plan literally says "Depends on: This proposal adopted,"
`lrh work-items readiness` does not check related-design adoption status at
all, and nothing here formally enforces the proposal's own stated
precondition. Treat proposal adoption as a strong recommendation before
starting implementation even though the tooling won't stop you either way.
Pick up once `round-cap-gate.md` and the three sibling skills it touches
have no other WI actively editing them concurrently.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-SKILLS-SELF-REVIEW.md`
  (does not exist yet — offered as follow-on, per Decision 7's governance
  choice: single-skill workstream, `WS-SKILLS-CONFIRM-FIXES` precedent)
- Design: `project/design/proposals/adopted/lrh-self-review/00_proposal.md`
- Backlog: `project/design/backlog.md` "Self-review-first tier..." entry
