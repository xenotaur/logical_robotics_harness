---
resolution: null
blocked_reason: null
blocked: false
id: WI-CLOSEOUT-EXPORT-WORK-REMAINS-CHAIN
title: Chain /lrh-closeout Step 8 to recommend /lrh-work-remains before /export
type: operation
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design: []
depends_on:
  - WI-SKILLS-LRH-WORK-REMAINS
blocked_by:
  - WI-SKILLS-LRH-WORK-REMAINS
expected_actions:
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - implement_lrh_work_remains
acceptance:
  - src/lrh/skills/lrh-closeout/SKILL.md Step 8 recommends running /lrh-work-remains before /export, in addition to (not replacing) the Pending-offers gate from WI-CLOSEOUT-EXPORT-SCOPE
  - .claude/skills/lrh-closeout/ is byte-for-byte identical to src/lrh/skills/lrh-closeout/
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-closeout/SKILL.md
  - .claude/skills/lrh-closeout/SKILL.md
---

## Summary

Once `/lrh-work-remains` exists (`WI-SKILLS-LRH-WORK-REMAINS`), add a second
layer to `/lrh-closeout` Step 8: recommend running `/lrh-work-remains` before
`/export`, since `/lrh-work-remains` has session-wide visibility that
`/lrh-closeout` structurally cannot have.

## Problem / Context

`WI-CLOSEOUT-EXPORT-SCOPE` (PR #519) gates `/lrh-closeout` Step 8's `/export`
offer on its own "Pending offers" list being empty — a self-contained,
immediate fix for the internal inconsistency observed closing out PR #516.
That gate narrows the scoping problem but does not close it: `/lrh-closeout`
is structurally scoped to one PR's artifact chain (its own PR, execution
records, WI, WS, proposal) and has no visibility into the rest of the
session — other open PRs, uncommitted files, stray/stale branches, unsaved
memories, or WIs proposed this session but unrelated to this closeout's
chain.

`WI-SKILLS-LRH-WORK-REMAINS` (currently `proposed`, not yet implemented) is
a strictly read-only, session-scoped reporting skill covering exactly this
gap via an 18-item checklist grounded in tracked repo state (git status/log,
`gh pr list/view`, `lrh snapshot current_focus`) — including "Incomplete
closeouts of PRs," "Untaken offers," "Open work items," "Unfinished
workstreams," and "Unsaved memories."

This item adds the Step 8 recommendation once that skill exists. It is
additive to, not a replacement for, `WI-CLOSEOUT-EXPORT-SCOPE`'s
Pending-offers gate.

**Prior art check:**
- *Duplication search:* no existing skill or work item chains
  `/lrh-closeout` to `/lrh-work-remains`. `WI-CLOSEOUT-EXPORT-SCOPE` (PR #519)
  addresses the narrower, self-contained part of this same Step 8 report;
  this item is deliberately scoped as its separate, dependency-gated
  follow-on rather than folded into it.
- *Demand search:* no existing backlog entry or proposal requests this
  specific chaining. Designed via `/lrh-design` this session alongside
  `WI-CLOSEOUT-EXPORT-SCOPE`.

## Scope

- `src/lrh/skills/lrh-closeout/SKILL.md` Step 8: add a recommendation to run
  `/lrh-work-remains` before `/export`, once that skill exists.
- Mirror to `.claude/skills/lrh-closeout/SKILL.md`.
- Exact wording and placement relative to the Pending-offers gate deferred
  to implementation time, once `/lrh-work-remains`'s actual output shape is
  known.

## Required Changes

1. Edit `src/lrh/skills/lrh-closeout/SKILL.md` Step 8 to add the
   `/lrh-work-remains` recommendation.
2. Copy the edited file to `.claude/skills/lrh-closeout/SKILL.md`.
3. Verify `diff -r src/lrh/skills/lrh-closeout/ .claude/skills/lrh-closeout/`
   is empty.

## Non-Goals

- Does not implement `/lrh-work-remains` itself — that is
  `WI-SKILLS-LRH-WORK-REMAINS`, a hard prerequisite.
- Does not remove or replace the Pending-offers gate from
  `WI-CLOSEOUT-EXPORT-SCOPE` — additive only.
- Does not automate invoking `/lrh-work-remains` from within
  `/lrh-closeout` — a recommendation/offer, not an automatic chain call,
  consistent with `/lrh-closeout`'s existing human-gated offer pattern.

## Acceptance Criteria

- `/lrh-closeout` Step 8 recommends `/lrh-work-remains` before `/export`,
  in addition to the existing Pending-offers gate
- `.claude/skills/lrh-closeout/` remains an exact copy of
  `src/lrh/skills/lrh-closeout/`
- `lrh validate` reports 0 errors

## Validation

- `lrh validate`
- `diff -r src/lrh/skills/lrh-closeout/ .claude/skills/lrh-closeout/`
