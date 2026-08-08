---
resolution: null
blocked_reason: null
blocked: false
id: WI-CLOSEOUT-EXPORT-SCOPE
title: Decouple /lrh-closeout Step 8 /export offer wording from Pending offers completion
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
  - src/lrh/skills/lrh-closeout/SKILL.md Step 8 always offers /export (never suppressed) but its wording no longer implies session completion when the Pending offers section is non-empty
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
to run `/export` unconditionally, phrased in a way that implies the
session's work is done, even in the same report where its own "Pending
offers" section lists work still outstanding. The fix decouples `/export`'s
wording from that completion implication — it does **not** withhold the
`/export` offer itself when offers are pending, since archiving is a
preservation action independent of whether follow-on work is finished, and
suppressing it risks the exact data-loss failure mode the session-archive
design already documents (see Problem/Context).

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
Pending offers list this same step already computes, a few lines above it.

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
walkthrough: root-cause analysis, options considered, and why this WI's
scope is the correct increment versus deferring to
`WI-SKILLS-LRH-WORK-REMAINS`).

**Revised during `/lrh-land` review-response (PR #519):** the original draft
of this WI *suppressed* the `/export` offer entirely when Pending offers was
non-empty. A reviewer (`chatgpt-codex-connector`) correctly flagged that this
risks permanent data loss: when the pending offer is follow-on work not
completed in the current session (exactly the PR #516 case), suppression
defers archiving the current transcript until after the user may have left
the session, and the session-archive design
(`project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md:65-72`)
already documents that exports are routinely skipped and a skipped capture
of a volatile local transcript can become permanent loss. `/export` archives
the current session; it does not assert follow-on work is complete. The
fix below was revised to keep the offer always available and only change its
*wording* — the report should identify unresolved offers separately (which
it already does, in the section directly above), not block the archival
action on them.

## Scope

- `src/lrh/skills/lrh-closeout/SKILL.md` Step 8: keep the `/export` offer
  bullet positioned after the "Pending offers" section (so its wording can
  reference that section's outcome), but do not suppress it. When Pending
  offers is non-empty, the offer text explicitly states that running
  `/export` now still archives this session's transcript and does not mean
  the listed offers are resolved.
- Add a short scoping-limitation note (in `SKILL.md`'s "What This Skill Does
  Not Do" or `references/closeout-workflow.md`) stating that `/lrh-closeout`
  has no session-wide visibility beyond its own PR/WI/WS/proposal chain —
  pointing to `WI-SKILLS-LRH-WORK-REMAINS` as the mechanism for full closure
  once implemented.
- Mirror both files to `.claude/skills/lrh-closeout/`.

## Required Changes

1. Edit `src/lrh/skills/lrh-closeout/SKILL.md` Step 8: keep the `/export`
   offer bullet after the "Pending offers" section; add conditional wording
   — when Pending offers is non-empty, state plainly that `/export` still
   archives this session and does not imply those offers are resolved; when
   empty, the offer text is unchanged from today.
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
- Does not suppress or withhold the `/export` offer under any condition —
  archival is decoupled from follow-on-offer completeness precisely because
  suppressing it risks the data-loss failure mode noted in Problem/Context.

## Acceptance Criteria

- `/lrh-closeout` Step 8 always offers `/export` (never suppressed); when
  Pending offers is non-empty, the offer's wording explicitly states that
  running it still archives this session and does not imply those offers
  are resolved
- The scoping-limitation note is present and references
  `WI-SKILLS-LRH-WORK-REMAINS`
- `.claude/skills/lrh-closeout/` is an exact copy of
  `src/lrh/skills/lrh-closeout/`
- `lrh validate` reports 0 errors

## Validation

- `lrh validate`
- `diff -r src/lrh/skills/lrh-closeout/ .claude/skills/lrh-closeout/`
