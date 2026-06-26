---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-LRH-DESIGN-STEP4
title: Update /lrh-design Step 4 with scope-assessment sub-step
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
  - WI-SKILLS-LRH-PROPOSAL
  - WI-SKILLS-LRH-WORKSTREAM
blocked_by: []
expected_actions:
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - implement_lrh_proposal
  - implement_lrh_workstream
acceptance:
  - Step 4 of .claude/skills/lrh-design/SKILL.md includes explicit scope-assessment sub-step with decision matrix
  - Step 4 offers to invoke /lrh-proposal and/or /lrh-workstream and/or /lrh-work-item based on assessed scope
  - Total SKILL.md line count remains under 500
  - lrh validate reports 0 errors
  - src/lrh/skills/lrh-design/SKILL.md and .claude/skills/lrh-design/SKILL.md are identical after edit
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-design/SKILL.md
  - .claude/skills/lrh-design/SKILL.md
---

## Summary

Edit the existing `/lrh-design` skill's Step 4 to add an explicit scope-
assessment sub-step with a decision matrix that selects the right combination
of `/lrh-proposal`, `/lrh-workstream`, and `/lrh-work-item` to offer the user
based on the design's scale and complexity.

## Problem / Context

`/lrh-design` Step 4 currently offers a generic "you might want a proposal"
mention with no guidance on when a proposal is warranted vs. work items alone
vs. a workstream. This leaves the user without actionable direction after the
design is produced. With `/lrh-proposal` and `/lrh-workstream` now available
as primitives, Step 4 can be made precise: assess the scope, apply the matrix,
offer the right artifact(s). Depends on `WI-SKILLS-LRH-PROPOSAL` and
`WI-SKILLS-LRH-WORKSTREAM` landing first so Step 4 can reference them by name.

## Scope

- Edit `src/lrh/skills/lrh-design/SKILL.md` Step 4 only
- Mirror the edit to `.claude/skills/lrh-design/SKILL.md`

## Required Changes

1. Edit `src/lrh/skills/lrh-design/SKILL.md` Step 4 — replace the current
   generic offer with a scope-assessment sub-step containing:
   - A decision matrix: single PR's worth → `/lrh-work-item` (ad-hoc or one
     item); multiple PRs, novel decisions, uncertain scope → `/lrh-proposal`
     ± `/lrh-workstream` ± `/lrh-work-item`; complex multi-stage with
     deferred scope → `/lrh-proposal` + `/lrh-workstream` first, work items
     later.
   - Explicit instruction to assess and offer, not automatically invoke.
   - Reference to `/lrh-proposal`, `/lrh-workstream`, and `/lrh-work-item`
     by name.
2. Mirror the same edit to `.claude/skills/lrh-design/SKILL.md`.

## Non-Goals

- Do not add new steps beyond Step 4 changes.
- Do not implement `/lrh-proposal` or `/lrh-workstream` within this item.
- Do not modify any other step in `lrh-design/SKILL.md`.
- Do not add `/lrh-capture-design` or any new skill in this item.

## Acceptance Criteria

- Step 4 of `.claude/skills/lrh-design/SKILL.md` includes an explicit scope-
  assessment sub-step with the decision matrix
- Step 4 offers to invoke `/lrh-proposal`, `/lrh-workstream`, and/or
  `/lrh-work-item` based on the assessed scope, with no automatic invocation
- Total `SKILL.md` line count remains under 500
- `lrh validate` reports 0 errors
- `src/lrh/skills/lrh-design/SKILL.md` and `.claude/skills/lrh-design/SKILL.md`
  are identical after the edit

## Validation

- `scripts/version tools`
- `lrh validate`
- `diff src/lrh/skills/lrh-design/SKILL.md .claude/skills/lrh-design/SKILL.md`

## Dependencies / Order

`WI-SKILLS-LRH-PROPOSAL` and `WI-SKILLS-LRH-WORKSTREAM` should land before
this item so Step 4 can reference the skills by their final names. The edit
is low-risk if done before they land (the names are known), but the
dependency is declared for correctness.
