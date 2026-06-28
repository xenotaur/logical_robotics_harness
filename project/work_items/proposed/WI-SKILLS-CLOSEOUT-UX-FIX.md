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

## Required Changes

TODO: flesh out with `lrh request ready-work-item`. Key changes expected:
- In `src/lrh/skills/lrh-closeout/SKILL.md` Step 8, add two report items:
  (a) confirmation of memory written (if Step 7 resulted in a write), with
  one-line summary of what was persisted
  (b) re-statement of any pending offers not yet acted on (e.g., offers
  declined or deferred at Step 4)
- Mirror changes to `.claude/skills/lrh-closeout/`

## Non-Goals

- Does not update any skill other than `/lrh-closeout` — the all-skills
  UX pass is a separate work item
- Does not change Step 7 behaviour — writing is still opt-in

## Acceptance Criteria

TODO: flesh out with `lrh request ready-work-item`.

## Validation

- `lrh validate`
- `diff -r src/lrh/skills/lrh-closeout/ .claude/skills/lrh-closeout/`
