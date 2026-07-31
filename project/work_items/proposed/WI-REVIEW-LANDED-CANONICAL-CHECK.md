---
resolution: null
blocked_reason: null
blocked: false
id: WI-REVIEW-LANDED-CANONICAL-CHECK
title: Forbid ad hoc timestamp filtering in review-landed checks; require canonical isResolved/commit_id source
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-EXECUTION-FRAMEWORK
related_design: []
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - write_docs
forbidden_actions:
  - force_push
  - delete_branch
  - implement_self_review_agent
  - merge_pr
acceptance:
  - "Each of /lrh-land, /lrh-review-response, /lrh-confirm-fixes SKILL.md states, in its review-landed/review-fetch step, that coverage is determined only via three sources -- isResolved state (from lrh github threads --mode raw --state all, filtered to isResolved == false; never lrh request review_response, which also excludes outdated threads), commit_id vs. current head (from the REST reviews call), and SHA-matched issue/review-body text for the no-thread case -- and never via a freehand since <timestamp> filter over comments/reviews/threads"
  - "/lrh-land Step 4's lastPush comparison is reworded so it cannot be read as authorizing a time-based exclusion filter on comment content"
  - "The motivating incident (a missed Copilot review on an earlier commit, due to a since-scoped check anchored to a later commit's push time) is cited in at least one edited skill as the concrete failure this prohibition prevents"
  - "src/ and .claude/ mirrors match for all three touched skills (diff -r reports no differences)"
  - "lrh validate reports 0 errors"
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-land/SKILL.md
  - .claude/skills/lrh-land/SKILL.md
  - src/lrh/skills/lrh-review-response/SKILL.md
  - .claude/skills/lrh-review-response/SKILL.md
  - src/lrh/skills/lrh-confirm-fixes/SKILL.md
  - .claude/skills/lrh-confirm-fixes/SKILL.md
---

## Summary

Harden the "has review landed / what does it cover" check in `/lrh-land`,
`/lrh-review-response`, and `/lrh-confirm-fixes` so it always reads the
canonical, unfiltered GitHub data (review-thread `isResolved` state, and
each review's `commit_id` compared to the current head) and never a
freehand `since <timestamp>` window applied to comments, reviews, or
threads. Add an explicit bright-line prohibition on ad hoc recency
filtering to each skill's review-landed language.

## Problem / Context

Two independent incidents show timestamp-based reasoning about review
coverage fails in both directions:

- PR #437 (documented in the acting agent's own cross-session memory as
  `feedback_review_coverage_check_commit_id` — an external record, not a
  path under this repo's `project/memory/` — and reflected in
  `lrh-confirm-fixes/SKILL.md:119`'s `isResolved`-filter language): a
  review looked "landed" by timestamp ordering, but its `commit_id`
  covered only the first of three commits — an old review over-credited
  as covering new work.
- This item's motivating incident: a live session scoped its review-landed
  check to "only since" a later commit's push time and missed a real,
  unresolved Copilot review with 5 inline findings that had landed
  promptly against an earlier commit — real, current review content
  under-credited as absent because a recency window excluded it.

Root cause: `src/lrh/integrations/github/pull_reviews.py:82-178`
(`get_pull_review_threads`/`get_pull_comments`) already fetches everything
unfiltered by time, and `lrh-confirm-fixes/SKILL.md:119` already specifies
filtering client-side on `isResolved`, not recency. The failure was
practice drift: a live session substituted an ad hoc recency-windowed
check for the documented mechanism. Nothing in the current skill text
explicitly forbids that substitution across all three call sites, so
nothing stops it recurring.

**Correction surfaced by this PR's own review, round 1 (Codex, P1):** an
earlier draft of this item described a single canonical command as the
source for both checks. That's wrong. `lrh request review_response`
(`request_service.py:122-144`) calls only `get_pull_review_threads()` —
whose GraphQL selection has `isResolved` but no `commit_id` — and never
calls `get_pull_comments()`. `isResolved` coverage and `commit_id`
coverage come from two different existing sources today, not one; the
skill wording this item specifies must name both explicitly rather than
implying a single command returns both.

**Second correction, surfaced by this PR's own review, round 2 (Codex, P1
x2):** round 1's correction above still named `lrh request
review_response` as the `isResolved` source — also wrong. That command's
own `formatters.has_threads_for_state(..., state="unresolved")`
(`formatters.py:31-40`) requires *both* `not isResolved` and `not
isOutdated`, so it silently hides genuinely unresolved-but-outdated
threads — the exact split this PR's own `_CONFIRM` execution record
observed directly (`lrh request review_response` reported "Nothing to
resolve" while `lrh github threads --mode raw --state all` filtered to
`isResolved == false` found the same 2 threads still open). The correct
`isResolved` source is `lrh github threads --mode raw --state all`,
filtered client-side to `isResolved == false` only — never `lrh request
review_response` for this purpose. Separately, a reviewer's response can
also arrive as a plain issue comment or review body with no distinct
thread at all (no `commit_id`, since it has no entry in
`/pulls/<N>/reviews`) — `lrh-confirm-fixes/SKILL.md:367-376` already
treats a SHA-matched instance of this as valid evidence. Coverage
therefore rests on **three** sources, not two: `isResolved` (via the
raw-threads command), `commit_id` vs. head (via the REST reviews call),
and SHA-matched issue/review-body text for the no-thread case.

### Duplication search

- In-repo: `WI-REVIEW-ROUND-ESCALATION-GATE` (proposed) touches the same
  `/lrh-confirm-fixes` Step 8 / `/lrh-land` area but solves a different
  problem (retrigger-batch cost-cap ceiling, not detection correctness of
  whether review has landed). No overlap; cross-linked, not folded in.
  The acting agent's own cross-session memory (external to this repo, not
  a `project/memory/` path) already documents the commit_id-vs-timestamp
  principle for the over-crediting direction, under the record name
  `feedback_review_coverage_check_commit_id`; this item extends the same
  principle to the under-crediting direction and makes it an explicit
  bright line in the skill text itself, not only an external memory note.
- Sibling repos / external libraries: none identified.
- Recommendation: proceed, standalone, cross-linked to
  `WI-REVIEW-ROUND-ESCALATION-GATE`.

### Demand search

- Work items: none found requesting this specific fix.
- Proposals: none found.
- Backlog (`project/design/backlog.md`): no matching entry for
  review-landed/timestamp-filter keywords.
- Recommendation: proceed.

## Scope

- Edit the review-landed / review-fetch language in the three skills to:
  1. Name the three canonical data sources for "has review landed and
     what does it cover":
     - `isResolved` coverage of unresolved findings — via `lrh github
       threads --mode raw --state all`, filtered client-side to
       `isResolved == false` only. Do not use `lrh request
       review_response` for this purpose: its own `state="unresolved"`
       filter (`formatters.py:31-40`) requires both `not isResolved`
       and `not isOutdated`, silently hiding genuinely
       unresolved-but-outdated threads.
     - `commit_id`-vs-head coverage — via the existing REST reviews
       call already used by `/lrh-confirm-fixes`:
       ```bash
       gh api repos/<owner>/<repo>/pulls/<N>/reviews \
         --jq '.[] | "\(.submitted_at) \(.user.login) \(.state) commit=\(.commit_id[0:7])"'
       ```
     - SHA-matched issue/review-body text, for a reviewer response with
       no distinct thread and therefore no `commit_id` — already
       recognized by `lrh-confirm-fixes/SKILL.md:367-376`; must be read
       and credited the same way there.
     Do not describe any pair of these as a single command or collapse
     them to two sources — each covers a case the others miss.
  2. State explicitly: never construct or apply a `since <timestamp>`
     filter over review comments, threads, or reviews when deciding
     whether review has landed or what it covers; only the three sources
     above determine that.
- Apply to all three call sites: `/lrh-land` Step 4
  (`lrh-land/SKILL.md:122-145`), `/lrh-review-response`'s review-fetch
  entry point, and `/lrh-confirm-fixes` Step 8's REVIEW-LANDED re-check
  (`lrh-confirm-fixes/SKILL.md:304-374`).

## Required Changes

1. `src/lrh/skills/lrh-land/SKILL.md` Step 4 — extend the `lastPush`
   comparison (lines ~132-140) so it cannot be read as license to filter
   comment content by time; make explicit that `lastPush` is only used to
   judge "have bots had time to run," never to exclude older-but-still-
   unresolved content. Replace its `lrh request review_response`-only
   check with the three-source model (raw-threads `isResolved`, REST
   `commit_id`, SHA-matched issue/review text).
2. `src/lrh/skills/lrh-review-response/SKILL.md` — add the same
   bright-line prohibition to its review-fetch step, naming all three
   sources explicitly.
3. `src/lrh/skills/lrh-confirm-fixes/SKILL.md` Step 8 — extend the
   existing `isResolved`-filter language (line 119) and the REVIEW-LANDED
   re-check (lines 304-374) with the explicit "never a since-filter"
   prohibition, citing this item's motivating incident. This skill
   already performs the `commit_id` REST check and already recognizes
   SHA-matched issue/review text (lines 367-376); cite both as the
   pattern `/lrh-land` and `/lrh-review-response` should follow.
4. Mirror all edits to `.claude/skills/lrh-land/`,
   `.claude/skills/lrh-review-response/`, `.claude/skills/lrh-confirm-fixes/`.

## Non-Goals

- Does not implement the self-review/assess-agent fallback discussed as
  "Phase 1" — separate future work item.
- Does not implement `WI-REVIEW-ROUND-ESCALATION-GATE`'s round-cap/ceiling
  mechanism — different problem (cost bounding vs. detection correctness),
  cross-linked only.
- Does not change `get_pull_review_threads`/`get_pull_comments`
  (`pull_reviews.py`) — already unfiltered by time; this item is
  documentation/process hardening only, not new tooling.
- Does not add automated enforcement/linting of the prohibition — relies
  on skill-text discipline, same as sibling rules in these skills today.

## Acceptance Criteria

- Each of `/lrh-land`, `/lrh-review-response`, `/lrh-confirm-fixes`
  SKILL.md states, in its review-landed/review-fetch step, that coverage
  is determined only via three sources — `isResolved` state (from `lrh
  github threads --mode raw --state all`, filtered to `isResolved ==
  false`; never `lrh request review_response`, which also excludes
  outdated threads), `commit_id` vs. current head (from the REST reviews
  call), and SHA-matched issue/review-body text for the no-thread case —
  and never via a freehand `since <timestamp>` filter.
- `/lrh-land` Step 4's `lastPush` comparison is reworded so it cannot be
  read as authorizing a time-based exclusion filter on comment content.
- The motivating incident is cited in at least one edited skill as the
  concrete failure this prohibition prevents.
- `src/` and `.claude/` mirrors match for all three touched skills
  (`diff -r` reports no differences).
- `lrh validate` reports 0 errors.

## Validation

- `lrh validate`
- `diff -r src/lrh/skills/lrh-land/ .claude/skills/lrh-land/`
- `diff -r src/lrh/skills/lrh-review-response/ .claude/skills/lrh-review-response/`
- `diff -r src/lrh/skills/lrh-confirm-fixes/ .claude/skills/lrh-confirm-fixes/`

## Risk Notes

- Wording-only fix: relies on the acting agent reading and following the
  strengthened instruction; it does not mechanically prevent an ad hoc
  timestamp filter the way a code-level guard would. If this recurs after
  the wording fix ships, that's evidence the fix needs to move from
  documentation to a non-discretionary tool wrapper.
- `/lrh-review-response` doesn't currently have as fleshed-out a
  REVIEW-LANDED step as `/lrh-land`/`/lrh-confirm-fixes` do; scope
  includes adding the prohibition there even though the surrounding step
  may need light restructuring to host it clearly.
