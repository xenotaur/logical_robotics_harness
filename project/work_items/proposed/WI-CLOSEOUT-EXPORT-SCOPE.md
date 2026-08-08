---
resolution: null
blocked_reason: null
blocked: false
id: WI-CLOSEOUT-EXPORT-SCOPE
title: Gate /lrh-closeout Step 8 /export offer on empty Pending-offers list
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
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - implement_wi_skills_lrh_work_remains
acceptance:
  - src/lrh/skills/lrh-closeout/SKILL.md Step 8 only offers /export when the Pending-offers section is empty; otherwise states /export is deferred until pending offers are resolved
  - src/lrh/skills/lrh-closeout/SKILL.md or references/closeout-workflow.md documents that /lrh-closeout is scoped to one PR's artifact chain and lacks session-wide visibility, pointing to WI-SKILLS-LRH-WORK-REMAINS for full closure
  - .claude/skills/lrh-closeout/ is byte-for-byte identical to src/lrh/skills/lrh-closeout/
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-closeout/SKILL.md
  - src/lrh/skills/lrh-closeout/references/closeout-workflow.md
  - .claude/skills/lrh-closeout/SKILL.md
  - .claude/skills/lrh-closeout/references/closeout-workflow.md
---

## Summary

Fix an internal inconsistency in `/lrh-closeout` Step 8: it currently offers
to run `/export` unconditionally, even in the same report where its own
"Pending offers" section lists work still outstanding. `/export` implies the
session's work is done; presenting it next to a non-empty Pending-offers list
contradicts that in the same message.

## Problem / Context

Closing out PR #516 this session, `/lrh-closeout` Step 8 offered `/export`
unconditionally while the same report's "Pending offers" section listed two
open items (a follow-on design-review kickoff, and implementing a work item
the closed-out PR had only proposed). Every other Step 8 line is properly
hedged on what the skill actually knows (`session_transcript: pending`
reminder is conditional, "Memory written" states yes/no explicitly, "Pending
offers" lists exactly what this run skipped) — `/export` is the one
unconditional, un-hedged claim in the step.

`/lrh-closeout` is correctly scoped to a single PR's artifact chain (PR, its
execution records, WI, WS, proposal) — that scoping is not itself a bug.
The bug is narrower: Step 8's `/export` line doesn't consult the
Pending-offers list this same step already computes, a few lines above it.

**Prior art check:**
- *Duplication search:* grepped `project/work_items/` and
  `project/design/backlog.md` for "export" — all hits concern the unrelated
  Codex/Antigravity conversation-export-manifest work
  (`WI-CODEX-CONVERSATION-EXPORT-*`, `WI-ANTIGRAVITY-CONVERSATION-EXPORT-*`).
  No existing work addresses the `/lrh-closeout` Step 8 `/export`-offer
  scoping problem.
- *Demand search:* grepped `project/workstreams/` and `project/design/` for
  `lrh-work-remains` / `WORK-REMAINS` — no hits beyond
  `WI-SKILLS-LRH-WORK-REMAINS` itself. No existing backlog entry requests
  this fix.

Designed via `/lrh-design` this session (see conversation for full framework
walkthrough: root-cause analysis, options considered, and why the
Pending-offers gate is the correct scope for this WI versus deferring to
`WI-SKILLS-LRH-WORK-REMAINS`).

## Scope

- `src/lrh/skills/lrh-closeout/SKILL.md` Step 8: reorder so the `/export`
  offer is decided after the Pending-offers section is computed; gate it on
  that section being empty.
- Add a short scoping-limitation note (in `SKILL.md`'s "What This Skill Does
  Not Do" or `references/closeout-workflow.md`) stating that `/lrh-closeout`
  has no session-wide visibility beyond its own PR/WI/WS/proposal chain, and
  that this gate narrows but does not close that gap — pointing to
  `WI-SKILLS-LRH-WORK-REMAINS` as the mechanism for full closure once
  implemented.
- Mirror both files to `.claude/skills/lrh-closeout/`.

## Required Changes

1. Edit `src/lrh/skills/lrh-closeout/SKILL.md` Step 8: move the `/export`
   offer bullet after the "Pending offers" section; add the empty-list
   condition and the deferred-language fallback.
2. Edit `src/lrh/skills/lrh-closeout/SKILL.md` (or
   `references/closeout-workflow.md`): add the scoping-limitation note.
3. Copy both edited files to `.claude/skills/lrh-closeout/` (byte-for-byte).
4. Verify `diff -r src/lrh/skills/lrh-closeout/ .claude/skills/lrh-closeout/`
   is empty.

## Non-Goals

- Does not implement `/lrh-work-remains` or any session-wide visibility
  mechanism — that is `WI-SKILLS-LRH-WORK-REMAINS`, tracked separately.
- Does not change any other Step 8 reporting line (session_transcript
  reminder, memory-written statement) — those are already correctly hedged.
- Does not change the Step 2/Step 4 closeout-plan assessment logic — only
  the Step 8 report.

## Acceptance Criteria

- `/lrh-closeout` Step 8 only offers `/export` when Pending offers is empty;
  otherwise states `/export` is deferred pending resolution of those offers
- The scoping-limitation note is present and references
  `WI-SKILLS-LRH-WORK-REMAINS`
- `.claude/skills/lrh-closeout/` is an exact copy of
  `src/lrh/skills/lrh-closeout/`
- `lrh validate` reports 0 errors

## Validation

- `lrh validate`
- `diff -r src/lrh/skills/lrh-closeout/ .claude/skills/lrh-closeout/`
