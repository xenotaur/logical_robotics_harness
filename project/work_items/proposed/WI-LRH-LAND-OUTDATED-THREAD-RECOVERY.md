---
resolution: null
blocked_reason: null
blocked: false
id: WI-LRH-LAND-OUTDATED-THREAD-RECOVERY
title: Governed outdated-thread recovery path in /lrh-land Step 4/5
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-SKILLS-EXECUTE
related_design:
  - project/design/proposals/proposed/outdated-thread-recovery/00_proposal.md
depends_on:
  - WI-REVIEW-RESPONSE-INCLUDE-THREAD
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - implement_automatic_exception
acceptance:
  - A newly-surfaced Unaddressed/Partial/Problematic-resolution outdated thread always presents a live three-way gate (fix now / defer / stop) before any recovery action -- never a silent "not a hard stop" path
  - Ambiguous and Problematic-comment buckets are excluded from the gate entirely -- hard rule, not a per-occurrence question
  - "The recovery path routes through /lrh-review-response's full protocol via --include-thread, not just its triage checks -- confirm gate, validation, and execution record all run"
  - /lrh-review-response's own feasibility check can reject the fix; a rejection is treated the same as Problematic-comment (surface, stop)
  - A same-land-run re-invocation of /lrh-review-response is a recognized non-blocking condition in its own Step 3, not a caller-side workaround
  - lrh validate reports 0 errors
  - diff -r src/lrh/skills/lrh-land/ .claude/skills/lrh-land/ and the lrh-review-response equivalent report no differences
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-land/SKILL.md
  - .claude/skills/lrh-land/SKILL.md
  - src/lrh/skills/lrh-review-response/SKILL.md
  - .claude/skills/lrh-review-response/SKILL.md
---

# Governed outdated-thread recovery path in `/lrh-land` Step 4/5

## Summary

Implement the live-gated, taxonomy-scoped outdated-thread recovery path
in `/lrh-land` Step 4/5, built on
`WI-REVIEW-RESPONSE-INCLUDE-THREAD`'s `--include-thread` flag.

## Problem / Context

`/lrh-confirm-fixes` can surface an outdated-but-unresolved thread that
`/lrh-land` Step 4's tooling never saw. PR #453's prose-only attempt at a
recovery path drew a P1 governance finding (could silently override the
human's stop-work condition) plus 8 more findings across 7 rounds, and
was reverted. `PROP-OUTDATED-THREAD-RECOVERY` designs the fix properly;
this item implements its Layer 2 (Decisions 2-5), depending on
`WI-REVIEW-RESPONSE-INCLUDE-THREAD` (Decision 1/Layer 1) landing first or
in the same PR.

### Duplication search
- In-repo: No existing implementation — the prior prose attempt was
  reverted in PR #453.
- Sibling repos: None identified (Taurcode checked; no matching
  mechanism).
- External libraries: None identified.
- Recommendation: Proceed.

### Demand search
- Work items: Found — `WI-REVIEW-RESPONSE-INCLUDE-THREAD` (sibling item,
  Layer 1 this item depends on).
- Proposals: Found — `PROP-OUTDATED-THREAD-RECOVERY` (this item
  implements its Layer 2).
- Backlog: Found — `project/design/backlog.md`, "`lrh request
  review_response` cannot surface a specific outdated-but-unresolved
  thread." This item, together with `WI-REVIEW-RESPONSE-INCLUDE-THREAD`,
  closes that entry.
- Recommendation: Close the backlog entry once both items land.

## Scope

- `/lrh-land` Step 5: replace the plain "not green = stop" rule's blind
  spot with an explicit, narrowly-scoped, always-live-gated exception for
  Unaddressed/Partial/Problematic-resolution outdated threads only.
- `/lrh-land` Step 4: note the new recovery path exists, pointing to
  Step 5.
- `/lrh-review-response` Step 3: recognize an in-session `/lrh-land`
  continuation as a non-blocking idempotence condition.
- Mirror all edits to `.claude/skills/`.

## Required Changes

1. `src/lrh/skills/lrh-land/SKILL.md` Step 5 — add the three-way gate
   (reusing `round-cap-gate.md`'s pattern), scoped to
   Unaddressed/Partial/Problematic-resolution; route the fix through
   `/lrh-review-response`'s full protocol via `--include-thread`;
   explicitly exclude Ambiguous/Problematic-comment.
2. `src/lrh/skills/lrh-land/SKILL.md` Step 4 — cross-reference the new
   Step 5 path.
3. `src/lrh/skills/lrh-review-response/SKILL.md` Step 3 — add the
   same-run-continuation non-blocking condition.
4. Mirror 1-3 to `.claude/skills/lrh-land/SKILL.md` and
   `.claude/skills/lrh-review-response/SKILL.md`.
5. Update `project/design/backlog.md` to mark the entry closed/linked to
   this item and `WI-REVIEW-RESPONSE-INCLUDE-THREAD`.

## Non-Goals

- Does not modify `/lrh-confirm-fixes`'s own taxonomy or Step 3
  classification logic.
- Does not implement `WI-REVIEW-RESPONSE-INCLUDE-THREAD`'s CLI change —
  depends on it.
- Does not add automatic (non-gated) recovery for any bucket, ever.

## Acceptance Criteria

- A newly-surfaced Unaddressed/Partial/Problematic-resolution outdated
  thread always presents a live three-way gate before any recovery
  action — never a silent "not a hard stop" path.
- Ambiguous and Problematic-comment buckets are excluded from the gate
  entirely — hard rule, not a per-occurrence question.
- The recovery path routes through `/lrh-review-response`'s full
  protocol via `--include-thread`, not just its triage checks — confirm
  gate, validation, and execution record all run.
- `/lrh-review-response`'s own feasibility check can reject the fix; a
  rejection is treated the same as Problematic-comment.
- A same-land-run re-invocation of `/lrh-review-response` is a
  recognized non-blocking condition in its own Step 3.
- `lrh validate` reports 0 errors.
- `diff -r` on both mirrored skill directories reports no differences.

## Validation

- `scripts/version tools`
- `lrh validate`
- `diff -r src/lrh/skills/lrh-land/ .claude/skills/lrh-land/`
- `diff -r src/lrh/skills/lrh-review-response/ .claude/skills/lrh-review-response/`

## Risk Notes

- This is prose-only (no new Python), so it has no automated test
  coverage of its own — verified by manual review and, ideally, a
  dogfooded real occurrence before being trusted, per this project's own
  "dogfood before shipping" practice.
- Risk of repeating PR #453's failure mode: keep the gate's scope narrow
  and resist adding further automatic branches under future review
  pressure.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-SKILLS-EXECUTE.md`
- Design: `project/design/proposals/proposed/outdated-thread-recovery/00_proposal.md`
