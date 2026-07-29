---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-LRH-LAND
title: Implement /lrh-land Claude Code skill
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
  - project/design/proposals/proposed/lrh-land-execute/00_proposal.md
  - project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md
  - src/lrh/skills/_shared/lifecycle-chain.md
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
  - implement_lrh_execute
  - implement_lrh_next
  - implement_lrh_run_tree
  - remove_confirm_gates
acceptance:
  - src/lrh/skills/lrh-land/SKILL.md exists with valid frontmatter
  - src/lrh/skills/lrh-land/references/land-workflow.md exists documenting the five glue-logic rules as a reference table
  - .claude/skills/lrh-land/ mirrors src/lrh/skills/lrh-land/ exactly (diff -r reports zero differences)
  - SKILL.md encodes the chain authorization gate at Step 2, before review-response and confirm-fixes
  - SKILL.md Step 6 (merge gate) states explicitly that the human executes the merge, not the agent
  - SKILL.md Step 4 (review-response) includes the REVIEW-LANDED check (empty comment list is not a clean review)
  - WI-SKILLS-LRH-LAND added to WS-SKILLS-EXECUTE.md work_items frontmatter list
  - /lrh-land entry added to CLAUDE.md ## Skills
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-land/SKILL.md
  - src/lrh/skills/lrh-land/references/land-workflow.md
  - .claude/skills/lrh-land/SKILL.md
  - .claude/skills/lrh-land/references/land-workflow.md
  - CLAUDE.md
  - project/workstreams/proposed/WS-SKILLS-EXECUTE.md
---

# Implement `/lrh-land` Claude Code skill

## Summary

Implement the `/lrh-land` skill as specified in `PROP-LRH-LAND-EXECUTE`
(Decision 3): a terminal pipeline skill that drives one open PR through the
complete end-of-lifecycle chain — chain authorization gate, review-response,
confirm-fixes, merge gate, and closeout — with all five glue-logic rules
encoded as explicit algorithmic steps rather than prose.

This is Phase 1 of `WS-SKILLS-EXECUTE`. It eliminates the primary friction
source documented in the LCATS full-lifecycle case study (nine PRs, ~35
manual skill-equivalent operations per session re-derived from scratch).

## Problem / Context

The LRH lifecycle chain ends with four skill-equivalent operations after
implementation: review-response, confirm-fixes, merge, and closeout.
Currently these are executed by re-reading each skill's `SKILL.md` and
issuing raw `git`/`gh`/`lrh` CLI calls from scratch in every session.
Five pieces of connecting glue logic are re-derived each run:

1. **Primary record selection** — searching `project/executions/` by `pr:`
   field and excluding `_REVIEW`, `_CONFIRM`, `_CLOSEOUT_NOTE` filename
   suffixes to identify the primary implementation record.
2. **Found-or-backfill** — determining whether an existing primary record was
   found (body is immutable; CHAIN-NOTE goes in a new `_CLOSEOUT_NOTE`
   record) or must be backfilled (backfill record authored directly).
3. **CHAIN-NOTE placement** — always written in the record being *authored*
   in the current run; never appended to an already-merged record body.
4. **Main-worktree-lock workaround** — landing commits to `main` when all
   worktrees have it checked out (`git fetch → checkout -b tmp → push
   tmp:main → delete tmp`).
5. **Stale-branch safety** — verifying `git diff origin/main <branch> --stat`
   reports zero net lines before reusing a planning-PR branch.

Note: `depends_on` enforcement (confirming all declared dependencies are
`resolved` before beginning implementation) is a Phase 2 concern handled by
`/lrh-execute`, not `/lrh-land`.

### Prior Art Check

#### Duplication search

- **In-repo:** No `/lrh-land` skill exists. `lifecycle-chain.md` and
  `DEC-DELIBERATE-CHAIN-INITIATION.md` name it as a planned future skill.
  No existing skill covers the full terminal chain.
- **Sibling repos:** Taurcode contains a `:land` master prompt. This WI
  implements that as a first-class LRH skill — not a duplication.
- **External libraries:** None applicable.
- **Recommendation:** Proceed.

#### Demand search

- **Work items:** `WI-DELIBERATE-MODEL-INVOCATION` (proposed,
  `WS-EXECUTION-FRAMEWORK`) enables Phase 2's direct sub-skill invocation
  but does not block Phase 1 — the interim inline pattern covers Phase 1
  without it.
- **Proposals:** `PROP-LRH-LAND-EXECUTE` (PR #427, merged 2026-07-28)
  governs this work item's scope.
- **Recommendation:** No action; the demand is satisfied by this WI.

## Scope

- Create `src/lrh/skills/lrh-land/SKILL.md` — the main skill file
  implementing the 8-step flow from PROP-LRH-LAND-EXECUTE Decision 3.
- Create `src/lrh/skills/lrh-land/references/land-workflow.md` — reference
  file containing the five glue-logic rules as an algorithmic reference
  table, the CHAIN-NOTE format, and the found-or-backfill decision matrix.
- Mirror both files byte-for-byte to `.claude/skills/lrh-land/`.
- Add `/lrh-land` entry to `CLAUDE.md ## Skills`.
- Add `WI-SKILLS-LRH-LAND` to `WS-SKILLS-EXECUTE.md` `work_items:` list.

## Required Changes

### `src/lrh/skills/lrh-land/SKILL.md`

New file. Frontmatter must include `name: lrh-land`, `description:` (one
line), and `when_to_use:` (invoke only when landing an open PR end-to-end).
Do **not** add `disable-model-invocation: true` — `/lrh-land` is a
planning/execution skill meant to be invokable by orchestrating skills.

Steps per PROP-LRH-LAND-EXECUTE Decision 3 (incorporating review-cycle
fixes from PR #427):

1. **Assess PR state** — verify PR is open; load execution records by `pr:`
   URL (grep `project/executions/`); apply primary-record selection rule
   (exclude filenames ending `_REVIEW.md`, `_CONFIRM.md`,
   `_CLOSEOUT_NOTE.md`); classify as found/backfill.
2. **Chain authorization gate** — elicit completion condition and stop-work
   condition per `DEC-DELIBERATE-CHAIN-INITIATION` before any automated
   link runs; show the full planned chain; wait for explicit approval.
3. **Resolve session transcript** — read `$CLAUDE_CODE_HOST_SESSION_ID`
   first; fall back to `list_sessions` filtered by PR number; then browser URL.
4. **Review-response** — check that review has actually completed (empty
   comment list immediately after push does not satisfy this check — it
   may mean review has not run yet); if completed with open comments,
   execute the review-response workflow inline (reading
   `/lrh-review-response/SKILL.md` steps; Phase 2 upgrade to direct
   `Skill` call after `WI-DELIBERATE-MODEL-INVOCATION` lands). If no
   open comments after review has completed, proceed to Step 5.
5. **Confirm-fixes** — execute the confirm-fixes workflow inline (same
   interim pattern); report verdict.
6. **Merge gate** — explicit in-session human authorization required;
   provide `gh pr merge <url> --merge` for the human to run; the agent
   does not execute the merge autonomously.
7. **Closeout** — execute the closeout workflow inline; encode CHAIN-NOTE
   placement rule (found primary: CHAIN-NOTE in new `_CLOSEOUT_NOTE`
   record with `rerun_of:`; no primary: CHAIN-NOTE in record being authored).
8. **Run journal** — append a structured YAML entry to the scratchpad run
   journal (format defined in `references/land-workflow.md`).

### `src/lrh/skills/lrh-land/references/land-workflow.md`

New reference file. Must document:

- **Five glue-logic rules** as a reference table (Logic / Rule format from
  PROP-LRH-LAND-EXECUTE Decision 3).
- **CHAIN-NOTE format** (`cycles=<N>; stops=<N>; gates=[...]; friction=...`).
- **Found-or-backfill matrix** (found → immutable body; CHAIN-NOTE in new
  `_CLOSEOUT_NOTE` record; not found → backfill directly in the authored
  record).
- **Run journal YAML skeleton** (minimum shape from PROP-LRH-LAND-EXECUTE
  Decision 8).
- **Interim invocation pattern note** — Steps 4–7 inline sub-skill steps
  and will be upgraded to direct `Skill` calls after
  `WI-DELIBERATE-MODEL-INVOCATION` lands.

### `.claude/skills/lrh-land/`

Byte-for-byte mirror of `src/lrh/skills/lrh-land/`. Verify with
`diff -r src/lrh/skills/lrh-land/ .claude/skills/lrh-land/`.

### `CLAUDE.md`

Add to `## Skills`:

```
- `/lrh-land` — Land an open PR end-to-end: chain auth gate, review, confirm, merge gate, closeout
```

### `project/workstreams/proposed/WS-SKILLS-EXECUTE.md`

Update `work_items:` from `[]` to `[WI-SKILLS-LRH-LAND]`.

## Non-Goals

- Does not implement `/lrh-execute` — that is Phase 2 (`WI-SKILLS-LRH-EXECUTE`).
- Does not implement `/lrh-next` or `/lrh-run-tree` — Phases 3–4.
- Does not remove or modify `disable-model-invocation` flags on any existing
  lifecycle skill — that is `WI-DELIBERATE-MODEL-INVOCATION`.
- Does not implement the `lrh prompt update-execution` CLI upgrade for the
  closeout inline step — deferred per PROP-LRH-CLOSEOUT Decision 1.
- Does not implement a run journal persistence mechanism beyond the scratchpad
  — the journal is a prototype per PROP-LRH-LAND-EXECUTE Decision 8.
- Does not add a typed `role:` field or validate `rerun_of:` as a foreign
  key in execution records — separate work items.

## Acceptance Criteria

- `src/lrh/skills/lrh-land/SKILL.md` exists with valid frontmatter
  (`name:`, `description:`, `when_to_use:`)
- `src/lrh/skills/lrh-land/references/land-workflow.md` exists and
  documents all five glue-logic rules as an algorithmic reference table
- `.claude/skills/lrh-land/` mirrors `src/lrh/skills/lrh-land/` exactly
  (`diff -r` reports zero differences)
- SKILL.md Step 2 is the chain authorization gate, preceding Steps 4–5
  (review-response and confirm-fixes)
- SKILL.md Step 4 (review-response) includes the REVIEW-LANDED check
  (empty comment list ≠ clean review)
- SKILL.md Step 6 (merge gate) states explicitly that the human executes
  the merge (`gh pr merge`), not the agent
- `WI-SKILLS-LRH-LAND` present in `WS-SKILLS-EXECUTE.md` `work_items:` list
- `/lrh-land` entry present in `CLAUDE.md ## Skills`
- `lrh validate` reports 0 errors

## Validation

- `diff -r src/lrh/skills/lrh-land/ .claude/skills/lrh-land/`
- `lrh validate`
- `grep "WI-SKILLS-LRH-LAND" project/workstreams/proposed/WS-SKILLS-EXECUTE.md`
- `grep "/lrh-land" CLAUDE.md`
- Manual review: SKILL.md Step 2 precedes Steps 4–5
- Manual review: SKILL.md Step 4 contains REVIEW-LANDED check
- Manual review: SKILL.md Step 6 states human executes merge
