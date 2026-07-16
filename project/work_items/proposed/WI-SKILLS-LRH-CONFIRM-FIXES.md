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

## Objective

Implement the `/lrh-confirm-fixes` skill as designed in `PROP-LRH-CONFIRM-FIXES`:
a pre-merge pass that independently verifies pushed review fixes against the
current `HEAD` diff, resolves the review threads the diff plainly satisfies,
surfaces the exceptions, and ends at a merge-readiness verdict without merging
the PR.

## Scope

Produce the skill following the `/lrh-*` project-local skill pattern
(`SKILL.md` + `references/`, confirm gate, "What This Skill Does Not Do"),
and wire the one-way handoff from `/lrh-review-response`.

### Deliverables

- `src/lrh/skills/lrh-confirm-fixes/SKILL.md` — 8-step flow per
  `PROP-LRH-CONFIRM-FIXES` Decision 13 (detect PR → gather state → fresh-eyes
  verification → confirm gate → execute resolutions → compute verdict →
  record + validate → readiness report), with `disable-model-invocation: true`
  and an `argument-hint` for the PR URL.
- `src/lrh/skills/lrh-confirm-fixes/references/confirm-fixes-workflow.md` —
  lifecycle placement, the verification taxonomy, the `gh api graphql`
  primitives (thread listing, `databaseId`→URL mapping, `resolveReviewThread`,
  `isResolved` check), the CI check (`gh pr checks --json name,state,bucket`,
  aggregated and re-checked post-push per Decision 8), the `_CONFIRM`
  execution-record convention with `rerun_of` population, and idempotency /
  re-run edge cases (Decision 14).
- `.claude/skills/lrh-confirm-fixes/` — byte-for-byte mirror of the `src/` tree.
- `CLAUDE.md ## Skills` — add the `/lrh-confirm-fixes` entry.

### Handoff wiring to `/lrh-review-response` (Decisions 9 and 11)

- Insert a `/lrh-confirm-fixes` node into the lifecycle diagram in
  `review-response-workflow.md`, between "repeat review rounds" and
  "Merge + closeout".
- Add a one-line next-step pointer to `/lrh-review-response`'s Step 7 report.
- Update `/lrh-review-response`'s `rerun_of` exclusion glob (in both `SKILL.md`
  and `review-response-workflow.md`) to exclude `_CONFIRM.md` in addition to
  `_REVIEW.md`, so a confirm record is never mismatched as a primary record.
- Mirror all `/lrh-review-response` edits to both `src/lrh/skills/` and
  `.claude/skills/`.

## Design Constraints

- **Verify against the live diff, not the execution record** (Decision 2) —
  independence is the whole point.
- **Exceptions are the product** (Decision 3) — resolve the clearly-satisfied
  threads as a batch; surface unaddressed / partial / ambiguous / problematic
  threads. Never resolve a thread the diff does not plainly satisfy.
- **Single batch confirm gate per run** (Decision 4) — not per-thread, not
  zero-gate.
- **Merge stays out of scope** (Decision 5) — end at a readiness verdict plus a
  `gh pr merge` one-liner; do not merge, do not trigger closeout.
- **Reuse `lrh request review_response`** for comment fetch and `gh api graphql`
  for thread operations (Decision 10) — no new CLI or `request_catalog.py`
  entry.

## Acceptance

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
