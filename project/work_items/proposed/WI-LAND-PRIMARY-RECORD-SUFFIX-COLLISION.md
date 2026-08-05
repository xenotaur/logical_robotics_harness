---
resolution: null
blocked_reason: null
blocked: false
id: WI-LAND-PRIMARY-RECORD-SUFFIX-COLLISION
title: Fix /lrh-land-family primary-record search substring-collision bug
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-SKILLS-EXECUTE
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
acceptance:
  - /lrh-land Step 1's primary-record search no longer misclassifies a primary record whose own topic slug ends in "review", "confirm", "closeout_note", or "selfreview" as absent
  - The same fix applies to /lrh-confirm-fixes's and /lrh-review-response's rerun_of searches, the documented sibling instance of the same bug
  - Fix distinguishes primary vs. side records by actual provenance (e.g. checking whether the record's own execution_id suffix was minted by the corresponding side-record-producing skill) rather than a bare filename-suffix substring match
  - land-workflow.md's "Known limitation, not fixed by this exclusion list" note is removed or updated to reflect the fix
  - A regression case exercises a primary record whose topic slug ends in one of the four reserved words and confirms it is still found by the corrected search
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-land/SKILL.md
  - src/lrh/skills/lrh-land/references/land-workflow.md
  - src/lrh/skills/lrh-confirm-fixes/SKILL.md
  - src/lrh/skills/lrh-confirm-fixes/references/confirm-fixes-workflow.md
  - src/lrh/skills/lrh-review-response/SKILL.md
  - src/lrh/skills/lrh-review-response/references/review-response-workflow.md
  - .claude/skills/lrh-land/SKILL.md
  - .claude/skills/lrh-land/references/land-workflow.md
  - .claude/skills/lrh-confirm-fixes/SKILL.md
  - .claude/skills/lrh-confirm-fixes/references/confirm-fixes-workflow.md
  - .claude/skills/lrh-review-response/SKILL.md
  - .claude/skills/lrh-review-response/references/review-response-workflow.md
---

# Fix `/lrh-land`-family primary-record search substring-collision bug

## Summary

`/lrh-land` Step 1, `/lrh-confirm-fixes`'s `rerun_of` search, and
`/lrh-review-response`'s `rerun_of` search all locate a PR's primary
execution record by excluding filenames ending in `_REVIEW.md`,
`_CONFIRM.md`, `_CLOSEOUT_NOTE.md`, and `_SELFREVIEW.md`. This exclusion is
a bare filename-suffix string match, not a check for the actual
slug-suffix construction convention those side-record-producing skills use
to append it. A **primary** record whose own topic slug happens to end in
one of those four words (e.g. a work item literally about "review",
"confirm," or "self-review") self-excludes from the search and is
misclassified as absent, incorrectly triggering the backfill path instead
of the found path.

## Problem / Context

This bug was hit three times in a single session landing
`WI-SKILLS-LRH-SELF-REVIEW` (PR #467) and its governing proposal PR #462
— both artifacts are themselves about "self-review," so their own primary
execution records' slugs end in `selfreview`/`self_review`, tripping the
same exclusion glob meant to filter out *side* records. Each time, the bug
was caught and worked around manually rather than fixed at the source.

The bug and workaround are already documented, but not fixed, in
`src/lrh/skills/lrh-land/references/land-workflow.md`'s "Found-or-Backfill
Matrix" section:

> **Known limitation, not fixed by this exclusion list:** these are bare
> filename-suffix matches, not a check for the actual slug-suffix
> convention that produces them. A primary record whose own topic slug
> happens to end in "review," "confirm," or "selfreview" self-excludes
> from this search...

### Prior Art Check

#### Duplication search

- **In-repo:** No existing work item tracks this bug as its own
  deliverable. `land-workflow.md`'s own note documents the limitation but
  explicitly defers the fix ("not fixed by this exclusion list").
  `WI-LRH-LAND-OUTDATED-THREAD-RECOVERY` (proposed, same workstream) fixes
  a different, unrelated `/lrh-land` gap.
- **Sibling repos:** Not applicable — this is specific to this project's
  own control-plane convention.
- **External libraries:** Not applicable.
- **Recommendation:** Proceed.

#### Demand search

- **Work items:** None found requesting this specific fix.
- **Proposals:** None found proposing this specific fix. The governing
  design for the affected skills (`PROP-LRH-LAND-EXECUTE`,
  `PROP-LRH-CONFIRM-FIXES`, `PROP-LRH-SELF-REVIEW`) does not address this
  bug.
- **Recommendation:** No existing artifact to close or link; proceed as a
  new work item.

## Scope

Fix the primary-vs-side-record classification logic used by
`/lrh-land` Step 1, `/lrh-confirm-fixes`'s `rerun_of` search, and
`/lrh-review-response`'s `rerun_of` search. Out of scope: any other
execution-record search or matching logic elsewhere in the harness not
enumerated above.

## Required Changes

1. Replace the bare filename-suffix `grep -v` exclusion in each of the
   three search sites with a check that distinguishes primary records from
   side records by actual provenance — for example, checking the
   candidate record's own `execution_id` (or slug) against the specific
   suffix-appending convention each side-record-producing skill uses
   (`-review`, `-confirm`, `-closeout-note`, `-selfreview` appended to an
   existing primary record's slug), rather than a bare "does the filename
   end with this string" test.
2. Update `land-workflow.md`'s "Found-or-Backfill Matrix" section to
   remove or correct the "Known limitation, not fixed by this exclusion
   list" note once the fix lands.
3. Add a regression case (in test coverage or as a documented manual
   verification step) covering a primary record whose topic slug ends in
   one of the four reserved words, confirming it is still found by the
   corrected search.
4. Mirror all `src/lrh/skills/` changes into their `.claude/skills/`
   counterparts exactly.

## Non-Goals

- Does not change the side-record suffix convention itself (`_REVIEW.md`,
  `_CONFIRM.md`, `_CLOSEOUT_NOTE.md`, `_SELFREVIEW.md`) — only how primary
  records are distinguished from them.
- Does not address any other execution-record search logic in the harness
  outside the three sites named above.
- Does not retroactively fix any already-landed execution record that was
  affected by this bug in a past session.

## Acceptance Criteria

- `/lrh-land` Step 1's primary-record search no longer misclassifies a
  primary record whose own topic slug ends in "review", "confirm",
  "closeout_note", or "selfreview" as absent
- The same fix applies to `/lrh-confirm-fixes`'s and
  `/lrh-review-response`'s `rerun_of` searches
- Fix distinguishes primary vs. side records by actual provenance rather
  than a bare filename-suffix substring match
- `land-workflow.md`'s "Known limitation, not fixed by this exclusion
  list" note is removed or updated to reflect the fix
- A regression case exercises a primary record whose topic slug ends in
  one of the four reserved words and confirms it is still found
- `lrh validate` reports 0 errors

## Validation

- lrh validate
- Manual or automated regression case per Required Change 3

## Risk Notes

The fix must not weaken the exclusion for genuine side records — a
provenance check that is too permissive could reintroduce the original
problem `_REVIEW.md`/`_CONFIRM.md`/etc. exclusion was meant to solve
(side records being misidentified as primary). Any implementation should
be verified against both directions: a genuine side record is still
excluded, and a primary record with a colliding slug suffix is no longer
excluded.
