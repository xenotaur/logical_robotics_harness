---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-LRH-CONFIRM-FIXES
title: Implement lrh-confirm-fixes Claude Code skill
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-SKILLS-CONFIRM-FIXES
related_design:
  - project/design/proposals/proposed/lrh-confirm-fixes/00_proposal.md
  - project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
acceptance:
  - src/lrh/skills/lrh-confirm-fixes/SKILL.md exists with valid frontmatter
  - src/lrh/skills/lrh-confirm-fixes/references/confirm-fixes-workflow.md exists
  - .claude/skills/lrh-confirm-fixes/ mirrors src/lrh/skills/lrh-confirm-fixes/ (diff -r reports no differences)
  - CLAUDE.md lists /lrh-confirm-fixes in the Skills section
  - /lrh-review-response lifecycle diagram and Step 7 report updated with the /lrh-confirm-fixes handoff pointer (both skill trees)
  - /lrh-review-response rerun_of exclusion glob updated to also exclude _CONFIRM.md (both skill trees)
  - WI-SKILLS-LRH-CONFIRM-FIXES present in WS-SKILLS-CONFIRM-FIXES.md work_items list
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-confirm-fixes/SKILL.md
  - src/lrh/skills/lrh-confirm-fixes/references/confirm-fixes-workflow.md
  - .claude/skills/lrh-confirm-fixes/SKILL.md
  - .claude/skills/lrh-confirm-fixes/references/confirm-fixes-workflow.md
  - CLAUDE.md
---

# Implement `/lrh-confirm-fixes` Claude Code skill

## Summary

Implement the `/lrh-confirm-fixes` skill as designed in `PROP-LRH-CONFIRM-FIXES`:
a pre-merge pass that independently verifies pushed review fixes against the
current `HEAD` diff, resolves the review threads the diff plainly satisfies,
surfaces the exceptions, and ends at a merge-readiness verdict without merging
the PR.

## Problem / Context

The LRH execution lifecycle today is `/lrh-implement → /lrh-review-response
(repeat) → [nothing] → human merges → /lrh-closeout`. No step independently
verifies that pushed fixes actually resolved the reviewers' comments, or marks
the review threads resolved. `/lrh-review-response` cannot fill this gap
itself — it writes the fixes, so a same-run verification would be
self-attestation. `/lrh-closeout` cannot either — it requires `state: MERGED`
and runs after the point where thread resolution matters. `PROP-LRH-CONFIRM-FIXES`
(`project/design/proposals/proposed/lrh-confirm-fixes/00_proposal.md`) captures
the full design: 14 decisions covering independence, the "exceptions are the
product" verification taxonomy, the single batch confirm gate, and why merge
stays explicitly out of scope. `WS-SKILLS-CONFIRM-FIXES` governs this
implementation.

## Scope

- Implement `/lrh-confirm-fixes` as a new project-local skill following the
  `/lrh-*` pattern (`SKILL.md` + `references/`, confirm gate, "What This
  Skill Does Not Do")
- Wire the one-way handoff pointer and `rerun_of` exclusion-glob fix into
  `/lrh-review-response`
- Mirror all changes to `.claude/skills/`

## Required Changes

1. Create `src/lrh/skills/lrh-confirm-fixes/SKILL.md` — 8-step flow per
   `PROP-LRH-CONFIRM-FIXES` Decision 13 (detect PR → gather state → fresh-eyes
   verification → confirm gate → execute resolutions → compute verdict →
   record + validate → readiness report), with `disable-model-invocation: true`
   and an `argument-hint` for the PR URL.
2. Create `src/lrh/skills/lrh-confirm-fixes/references/confirm-fixes-workflow.md` —
   lifecycle placement, the verification taxonomy, the `gh api graphql`
   primitives (thread listing, `databaseId`→URL mapping, `resolveReviewThread`,
   `isResolved` check), the CI check (`gh pr checks --json name,state,bucket`,
   aggregated and re-checked post-push per Decision 8), the `_CONFIRM`
   execution-record convention with `rerun_of` population, and idempotency /
   re-run edge cases (Decision 14).
3. Mirror both files to `.claude/skills/lrh-confirm-fixes/`.
4. Add a `/lrh-confirm-fixes` index entry to `CLAUDE.md ## Skills`.
5. Insert a `/lrh-confirm-fixes` node into the lifecycle diagram in
   `src/lrh/skills/lrh-review-response/references/review-response-workflow.md`,
   between "repeat review rounds" and "Merge + closeout".
6. Add a one-line next-step pointer to `/lrh-review-response`'s Step 7 report
   in `src/lrh/skills/lrh-review-response/SKILL.md`.
7. Update `/lrh-review-response`'s `rerun_of` exclusion glob (in both
   `SKILL.md` and `review-response-workflow.md`) to exclude `_CONFIRM.md` in
   addition to `_REVIEW.md`, so a confirm record is never mismatched as a
   primary record.
8. Mirror steps 5–7 to `.claude/skills/lrh-review-response/`.
9. Add `WI-SKILLS-LRH-CONFIRM-FIXES` to `WS-SKILLS-CONFIRM-FIXES.md`'s
   `work_items:` list (it is already present; confirm on landing).

## Design Constraints

- **Verify against the live diff, not the execution record** (Decision 2) —
  independence is the whole point.
- **Exceptions are the product** (Decision 3) — resolve the clearly-satisfied
  threads as a batch; surface unaddressed / partial / ambiguous / problematic
  threads. Never resolve a thread the diff does not plainly satisfy.
- **Single batch confirm gate per run** (Decision 4) — not per-thread, not
  zero-gate.
- **Reuse `lrh request review_response`** for comment fetch and `gh api graphql`
  for thread operations (Decision 10) — no new CLI or `request_catalog.py`
  entry.

## Non-Goals

- Does not merge the PR — end at a readiness verdict plus a `gh pr merge`
  one-liner; merge stays a human action (Decision 5).
- Does not trigger `/lrh-closeout` — closeout runs post-merge.
- Does not resolve any thread the diff does not plainly satisfy — ambiguous,
  partial, and problematic threads are surfaced, never guess-resolved.
- Does not silently loop `/lrh-review-response` — unaddressed threads are
  detected and the fix skill is offered, not auto-invoked.
- Does not modify `lrh request review_response` or its template, and does not
  add a new `lrh request` catalog entry.

## Acceptance Criteria

- `src/lrh/skills/lrh-confirm-fixes/SKILL.md` exists with valid frontmatter
- `src/lrh/skills/lrh-confirm-fixes/references/confirm-fixes-workflow.md` exists
- `diff -r src/lrh/skills/lrh-confirm-fixes/ .claude/skills/lrh-confirm-fixes/`
  reports no differences
- `CLAUDE.md` lists `/lrh-confirm-fixes` in the Skills section
- `/lrh-review-response` lifecycle diagram and Step 7 report updated with the
  handoff pointer (both skill trees)
- `/lrh-review-response` `rerun_of` exclusion glob updated to also exclude
  `_CONFIRM.md` (both skill trees)
- `WI-SKILLS-LRH-CONFIRM-FIXES` present in `WS-SKILLS-CONFIRM-FIXES.md`
  `work_items` list
- `lrh validate` reports 0 errors

## Validation

- `scripts/version tools`
- `lrh validate`
- `diff -r src/lrh/skills/lrh-confirm-fixes/ .claude/skills/lrh-confirm-fixes/`
- `diff -r src/lrh/skills/lrh-review-response/ .claude/skills/lrh-review-response/`
