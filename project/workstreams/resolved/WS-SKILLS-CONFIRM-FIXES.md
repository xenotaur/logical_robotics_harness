---
id: WS-SKILLS-CONFIRM-FIXES
kind: planning_node
title: LRH Pre-Merge Verification Skill
status: resolved
stage: closed
origin: follow_up
summary: >
  Implement the /lrh-confirm-fixes skill, a pre-merge pass that independently
  verifies pushed review fixes against the current HEAD diff, resolves the
  review threads the diff plainly satisfies, surfaces the exceptions, and ends
  at a merge-readiness verdict without merging the PR.
related_design:
  - project/design/proposals/proposed/lrh-confirm-fixes/00_proposal.md
  - project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md
work_items:
  - WI-SKILLS-LRH-CONFIRM-FIXES
exit_criteria:
  - /lrh-confirm-fixes skill exists at .claude/skills/lrh-confirm-fixes/ and src/lrh/skills/lrh-confirm-fixes/ and passes lrh validate with 0 errors
  - diff -r src/lrh/skills/lrh-confirm-fixes/ .claude/skills/lrh-confirm-fixes/ reports no differences
  - CLAUDE.md ## Skills index updated with /lrh-confirm-fixes entry
  - /lrh-review-response lifecycle diagram and Step 7 report updated with the /lrh-confirm-fixes handoff pointer (both skill trees)
  - /lrh-review-response rerun_of exclusion glob updated to also exclude _CONFIRM.md (both skill trees)
  - WI-SKILLS-LRH-CONFIRM-FIXES resolved in project/work_items/resolved/
---

## Purpose

This workstream implements `/lrh-confirm-fixes`, the missing pre-merge
verification complement to `/lrh-implement` and `/lrh-review-response` in the
LRH execution lifecycle. The skill sits after the last `/lrh-review-response`
round and before the human merge — the `[nothing]` gap in the lifecycle
diagram — and independently verifies that pushed fixes resolved the reviewers'
comments, resolving the threads the current `HEAD` diff plainly satisfies and
surfacing the exceptions.

## Background / Rationale

The design is captured in `PROP-LRH-CONFIRM-FIXES` (proposed 2026-07-15). Two
forces motivate it: reviewer burden (when most comments and most responses are
valid, ratifying each thread by hand buries the one that needs a human eye —
"exceptions are the product"), and the value of verification before an
irreversible merge (a recent downstream PR had a real packaging bug caught by
reviewers pre-merge). The skill cannot live inside `/lrh-review-response`
(which writes the fixes and so cannot independently judge them) or
`/lrh-closeout` (which requires `state: MERGED` and runs too late), so it is a
new skill.

## Scope

- Implement `/lrh-confirm-fixes` skill: 8-step flow (detect PR → gather state →
  fresh-eyes verification → confirm gate → execute resolutions → compute verdict
  → record + validate → readiness report), with one reference file
  (`confirm-fixes-workflow.md`)
- Deliver distributable package copies at `src/lrh/skills/lrh-confirm-fixes/`
  for global installation via `lrh setup`, mirrored byte-for-byte to
  `.claude/skills/lrh-confirm-fixes/`
- Wire the handoff in `/lrh-review-response` (lifecycle diagram node + Step 7
  pointer) and update its `rerun_of` exclusion glob to also exclude
  `_CONFIRM.md`, in both skill trees
- Reuse `lrh request review_response` for comment fetch and `gh api graphql`
  for thread listing and resolution — no new CLI or request-catalog entry

## Work Items

- **`WI-SKILLS-LRH-CONFIRM-FIXES`** — Implement `/lrh-confirm-fixes` skill.
  Produces `src/lrh/skills/lrh-confirm-fixes/SKILL.md`,
  `references/confirm-fixes-workflow.md`, the `.claude/skills/lrh-confirm-fixes/`
  mirror, the `CLAUDE.md` index entry, and the `/lrh-review-response` handoff
  and glob edits.

## Exit Criteria

- `/lrh-confirm-fixes` skill exists at `.claude/skills/lrh-confirm-fixes/` and
  `src/lrh/skills/lrh-confirm-fixes/` and passes `lrh validate` with 0 errors
- `diff -r src/lrh/skills/lrh-confirm-fixes/ .claude/skills/lrh-confirm-fixes/`
  reports no differences
- `CLAUDE.md ## Skills` index updated with `/lrh-confirm-fixes` entry
- `/lrh-review-response` lifecycle diagram and Step 7 report updated with the
  `/lrh-confirm-fixes` handoff pointer (both skill trees)
- `/lrh-review-response` `rerun_of` exclusion glob updated to also exclude
  `_CONFIRM.md` (both skill trees)
- `WI-SKILLS-LRH-CONFIRM-FIXES` resolved in `project/work_items/resolved/`

## Non-Goals

- Does not merge the PR or trigger closeout — merge stays a human action; the
  skill ends at a readiness verdict plus a `gh pr merge` one-liner
- Does not resolve any thread the diff does not plainly satisfy — ambiguous,
  partial, and problematic threads are surfaced, never guess-resolved
- Does not add a new `lrh request` template or CLI command — reuses
  `lrh request review_response` and `gh api graphql`
- Does not modify `/lrh-review-response`'s triage protocol — only wires the
  handoff pointer and the `rerun_of` exclusion glob
