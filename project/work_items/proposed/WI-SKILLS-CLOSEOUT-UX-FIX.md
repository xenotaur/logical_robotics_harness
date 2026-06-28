---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-CLOSEOUT-UX-FIX
title: Echo mid-skill offers in /lrh-closeout final report
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-SKILLS-CLOSEOUT
related_design:
  - project/design/proposals/adopted/lrh-closeout/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
acceptance: []
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected: []
---

## Summary

Update `/lrh-closeout` Step 8 (report) to echo any memory written in Step 7
and re-state any offers that were made mid-skill but may not have been acted
on. This ensures the final report is the authoritative summary of what
happened and what remains open — users who skim to the end don't miss offers
buried earlier in the output.

## Problem / Context

In the 2026-06-27 closeout session, Step 7 asked about memory and Step 8
produced the full report. The memory offer was answered and acted upon, but
the report did not confirm this. A user reading the report for the first time
would not know whether memory was written or not.

This is a general UX issue: skills that make optional offers mid-execution
(memory writing, WI→WS linking, session_transcript updates) bury those offers
before the report appears. Nielsen Norman Group's progressive disclosure
research supports placing high-priority actionable items where users look last.

The issue is cross-cutting (all 10 skills carry the pattern), but this WI
scopes the fix to `/lrh-closeout` only. Other skills are a separate concern.

## Scope

- `src/lrh/skills/lrh-closeout/SKILL.md` — Step 8 report section only
- `.claude/skills/lrh-closeout/SKILL.md` — byte-for-byte mirror

## Required Changes

1. **`SKILL.md` Step 8 — report section**: add two items after the existing
   bullet list:
   (a) **Memory confirmation:** "Memory written: [one-line summary]" if Step 7
   resulted in a write; "Memory: nothing written this session" if the user
   declined. This makes the Step 7 outcome visible to anyone who skims to
   the end of the output.
   (b) **Pending offers:** re-state any actions that were offered during the
   skill run but not included in the confirmed plan — e.g., WS closeout
   skipped (not all WIs resolved), proposal adoption skipped (WS not
   closing), or any offer the user deferred at Step 4. Format:
   "Pending: [offer] — [reason it was not actioned]".

2. **Mirror** all changes byte-for-byte to `.claude/skills/lrh-closeout/`.

## Out of Scope

- Does not update any skill other than `/lrh-closeout` — the all-skills
  UX pass is a separate work item
- Does not change Step 7 behaviour — writing is still opt-in
- Does not add new offers; only surfaces offers already made earlier in the
  same skill run

## Likely Files

- `src/lrh/skills/lrh-closeout/SKILL.md` (Step 8)
- `.claude/skills/lrh-closeout/SKILL.md` (mirror)

## Acceptance Criteria

- `/lrh-closeout` Step 8 report includes a memory bullet confirming whether
  Step 7 resulted in a write (with one-line summary) or not.
- `/lrh-closeout` Step 8 report includes a pending-offers section re-stating
  any action offered but not confirmed during the skill run (WS closeout
  skipped, proposal adoption skipped, etc.).
- `diff -r src/lrh/skills/lrh-closeout/ .claude/skills/lrh-closeout/`
  reports no differences.
- `lrh validate` reports 0 errors.

## Validation

- `lrh validate`
- `diff -r src/lrh/skills/lrh-closeout/ .claude/skills/lrh-closeout/`
