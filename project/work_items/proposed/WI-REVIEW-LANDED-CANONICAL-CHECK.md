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
  - "Each of /lrh-land, /lrh-review-response, /lrh-confirm-fixes SKILL.md states, in its review-landed/review-fetch step, that coverage is determined only via isResolved state (from lrh request review_response) and commit_id vs. current head (from the REST reviews call) -- two distinct sources, not implied to be one command -- and never via a freehand since <timestamp> filter over comments/reviews/threads"
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

**Correction surfaced by this PR's own review (Codex, P1):** an earlier
draft of this item described a single canonical command as the source for
both checks. That's wrong. `lrh request review_response`
(`request_service.py:122-144`) calls only `get_pull_review_threads()` —
whose GraphQL selection has `isResolved` but no `commit_id` — and never
calls `get_pull_comments()`. `isResolved` coverage and `commit_id`
coverage come from two different existing sources today, not one; the
skill wording this item specifies must name both explicitly rather than
implying a single command returns both.

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
  1. Name the two canonical data sources for "has review landed and what
     does it cover" — `lrh request review_response` (backed by
     `get_pull_review_threads()`) for unresolved-thread coverage via
     `isResolved`, and the existing REST reviews call already used by
     `/lrh-confirm-fixes` (`gh api repos/<owner>/<repo>/pulls/<N>/reviews
     --jq '.[] | "\(.submitted_at) \(.user.login) \(.state)
     commit=\(.commit_id[0:7])"'`) for `commit_id`-vs-head coverage. Do
     not describe these as a single command — `lrh request
     review_response` does not expose `commit_id`.
  2. State explicitly: never construct or apply a `since <timestamp>`
     filter over review comments, threads, or reviews when deciding
     whether review has landed or what it covers; only `isResolved`
     (coverage of unresolved findings, via `lrh request review_response`)
     and `commit_id` vs. current head (coverage of the current commit,
     via the REST reviews call) determine that.
- Apply to all three call sites: `/lrh-land` Step 4
  (`lrh-land/SKILL.md:122-145`), `/lrh-review-response`'s review-fetch
  entry point, and `/lrh-confirm-fixes` Step 8's REVIEW-LANDED re-check
  (`lrh-confirm-fixes/SKILL.md:304-374`).

## Required Changes

1. `src/lrh/skills/lrh-land/SKILL.md` Step 4 — extend the `lastPush`
   comparison (lines ~132-140) so it cannot be read as license to filter
   comment content by time; make explicit that `lastPush` is only used to
   judge "have bots had time to run," never to exclude older-but-still-
   unresolved content. Add the `commit_id`-vs-head REST check (the same
   call already used in `/lrh-confirm-fixes`) as the named source for
   commit coverage, since `lrh request review_response` does not provide
   it.
2. `src/lrh/skills/lrh-review-response/SKILL.md` — add the same
   bright-line prohibition to its review-fetch step, naming both sources
   explicitly (`isResolved` via `lrh request review_response`; `commit_id`
   via the REST reviews call).
3. `src/lrh/skills/lrh-confirm-fixes/SKILL.md` Step 8 — extend the
   existing `isResolved`-filter language (line 119) and the REVIEW-LANDED
   re-check (lines 304-374) with the explicit "never a since-filter"
   prohibition, citing this item's motivating incident. This skill
   already performs the `commit_id` REST check; cite it as the pattern
   `/lrh-land` and `/lrh-review-response` should follow.
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
  is determined only via `isResolved` state (from `lrh request
  review_response`) and `commit_id` vs. current head (from the REST
  reviews call) — two distinct sources, not implied to be one command —
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
