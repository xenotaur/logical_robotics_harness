---
resolution: null
blocked_reason: null
blocked: false
id: WI-PAC-DESIGN-SKILLS
title: Wire prior-art check into lrh-design, lrh-proposal, lrh-workstream
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-PRIOR-ART-CHECK
related_design: []
depends_on:
  - WI-PAC-SHARED-REFERENCE
blocked_by: []
expected_actions:
  - create_file
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - implement_wi_pac_impl_skills
acceptance:
  - src/lrh/skills/_shared/prior-art-check.md exists (from WI-PAC-SHARED-REFERENCE)
  - Each of lrh-design, lrh-proposal, lrh-workstream has references/prior-art-check.md with synced-copy header comment
  - lrh-design SKILL.md Step 3a includes the prior-art check as an explicit required sub-step
  - lrh-proposal and lrh-workstream body guides include a required Prior Art Check section
  - diff -r src/lrh/skills/lrh-design/ .claude/skills/lrh-design/ reports no differences
  - diff -r src/lrh/skills/lrh-proposal/ .claude/skills/lrh-proposal/ reports no differences
  - diff -r src/lrh/skills/lrh-workstream/ .claude/skills/lrh-workstream/ reports no differences
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-design/references/prior-art-check.md
  - .claude/skills/lrh-design/references/prior-art-check.md
  - src/lrh/skills/lrh-design/SKILL.md
  - .claude/skills/lrh-design/SKILL.md
  - src/lrh/skills/lrh-proposal/references/prior-art-check.md
  - .claude/skills/lrh-proposal/references/prior-art-check.md
  - src/lrh/skills/lrh-proposal/references/proposal-body-guide.md
  - .claude/skills/lrh-proposal/references/proposal-body-guide.md
  - src/lrh/skills/lrh-proposal/SKILL.md
  - .claude/skills/lrh-proposal/SKILL.md
  - src/lrh/skills/lrh-workstream/references/prior-art-check.md
  - .claude/skills/lrh-workstream/references/prior-art-check.md
  - src/lrh/skills/lrh-workstream/references/workstream-body-guide.md
  - .claude/skills/lrh-workstream/references/workstream-body-guide.md
  - src/lrh/skills/lrh-workstream/SKILL.md
  - .claude/skills/lrh-workstream/SKILL.md
---

## Summary

Copy `_shared/prior-art-check.md` into `lrh-design`, `lrh-proposal`, and
`lrh-workstream` and update each skill's SKILL.md and/or body guide to make
the prior-art check a required step.

## Problem / Context

These three skills create durable design commitments (design docs, proposals,
workstream planning nodes) but have no structured check for prior art or
existing implementations. Depends on `WI-PAC-SHARED-REFERENCE` for the
canonical procedure content.

## Scope

- Copy `_shared/prior-art-check.md` into each skill's `references/`
  (both `src/lrh/skills/` and `.claude/skills/`), with synced-copy header
  comment naming the `_shared/` master
- Update `lrh-design` SKILL.md Step 3a to explicitly require the prior-art
  check before proceeding to best practices
- Update `lrh-proposal` and `lrh-workstream` body guides and SKILL.md
  interview steps to include a `## Prior Art Check` body section

## Required Changes

- `src/lrh/skills/lrh-design/references/prior-art-check.md` — new (copy)
- `.claude/skills/lrh-design/references/prior-art-check.md` — new (copy)
- `src/lrh/skills/lrh-design/SKILL.md` — add prior-art sub-step to Step 3a
- `.claude/skills/lrh-design/SKILL.md` — mirror of above
- `src/lrh/skills/lrh-proposal/references/prior-art-check.md` — new (copy)
- `.claude/skills/lrh-proposal/references/prior-art-check.md` — new (copy)
- `src/lrh/skills/lrh-proposal/references/proposal-body-guide.md` — add `## Prior Art Check` section
- `.claude/skills/lrh-proposal/references/proposal-body-guide.md` — mirror of above
- `src/lrh/skills/lrh-proposal/SKILL.md` — add reference to prior-art-check.md in Reference Knowledge
- `.claude/skills/lrh-proposal/SKILL.md` — mirror of above
- `src/lrh/skills/lrh-workstream/references/prior-art-check.md` — new (copy)
- `.claude/skills/lrh-workstream/references/prior-art-check.md` — new (copy)
- `src/lrh/skills/lrh-workstream/references/workstream-body-guide.md` — add `## Prior Art Check` section
- `.claude/skills/lrh-workstream/references/workstream-body-guide.md` — mirror of above
- `src/lrh/skills/lrh-workstream/SKILL.md` — add reference to prior-art-check.md in Reference Knowledge
- `.claude/skills/lrh-workstream/SKILL.md` — mirror of above

## Non-Goals

- Does not wire into `lrh-work-item` or `lrh-implement` — that is `WI-PAC-IMPL-SKILLS`
- Does not add automated drift-checking between the `_shared/` master and copies

## Acceptance Criteria

- Each of `lrh-design`, `lrh-proposal`, `lrh-workstream` has
  `references/prior-art-check.md` in both `src/lrh/skills/` and `.claude/skills/`
  with a synced-copy header comment
- `lrh-design` SKILL.md Step 3a includes the prior-art check as an explicit
  required sub-step before best-practices review
- `lrh-proposal` and `lrh-workstream` body guides include a required
  `## Prior Art Check` section
- `lrh validate` reports 0 errors

## Validation

- `lrh validate`
