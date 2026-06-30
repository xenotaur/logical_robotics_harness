---
resolution: null
blocked_reason: null
blocked: false
id: WI-PAC-IMPL-SKILLS
title: Wire prior-art check into lrh-work-item and lrh-implement
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
acceptance:
  - lrh-work-item research step extended to cover code/library duplication with verdict recorded in work item body
  - lrh-implement SKILL.md has a Step 1.5 that validates or performs the prior-art check before implementation begins
  - Each of lrh-work-item and lrh-implement has references/prior-art-check.md with synced-copy header comment
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-work-item/references/prior-art-check.md
  - .claude/skills/lrh-work-item/references/prior-art-check.md
  - src/lrh/skills/lrh-work-item/SKILL.md
  - .claude/skills/lrh-work-item/SKILL.md
  - src/lrh/skills/lrh-work-item/references/work-item-body-guide.md
  - .claude/skills/lrh-work-item/references/work-item-body-guide.md
  - src/lrh/skills/lrh-implement/references/prior-art-check.md
  - .claude/skills/lrh-implement/references/prior-art-check.md
  - src/lrh/skills/lrh-implement/SKILL.md
  - .claude/skills/lrh-implement/SKILL.md
---

## Summary

Copy `_shared/prior-art-check.md` into `lrh-work-item` and `lrh-implement`
and update each skill to include the prior-art check in its workflow.

## Problem / Context

`lrh-work-item`'s existing research step checks for duplicate work items but
not for duplicate code or external libraries. `lrh-implement` has no prior-art
step at all — it assumes the work item already scoped this correctly. Depends
on `WI-PAC-SHARED-REFERENCE` for the canonical procedure content.

## Scope

- Copy `_shared/prior-art-check.md` into each skill's `references/`
  (both `src/lrh/skills/` and `.claude/skills/`), with synced-copy header
- Extend `lrh-work-item` SKILL.md Step 3 to explicitly cover code/library
  duplication (not just duplicate work items) and record the verdict in the
  work item's `## Problem / Context` body section
- Update `lrh-work-item` body guide to document the verdict format
- Add Step 1.5 to `lrh-implement` SKILL.md: validate that a prior-art check
  was performed (present in the WI body), or perform a quick check if the WI
  predates this change — warn-don't-block, matching the readiness-check
  precedent at Step 1

## Required Changes

- `src/lrh/skills/lrh-work-item/references/prior-art-check.md` — new (copy)
- `.claude/skills/lrh-work-item/references/prior-art-check.md` — new (copy)
- `src/lrh/skills/lrh-work-item/SKILL.md` — extend Step 3 and Reference Knowledge
- `.claude/skills/lrh-work-item/SKILL.md` — mirror of above
- `src/lrh/skills/lrh-work-item/references/work-item-body-guide.md` — document verdict format in `## Problem / Context` section
- `.claude/skills/lrh-work-item/references/work-item-body-guide.md` — mirror of above
- `src/lrh/skills/lrh-implement/references/prior-art-check.md` — new (copy)
- `.claude/skills/lrh-implement/references/prior-art-check.md` — new (copy)
- `src/lrh/skills/lrh-implement/SKILL.md` — add Step 1.5
- `.claude/skills/lrh-implement/SKILL.md` — mirror of above

## Non-Goals

- Does not add automated drift-checking between `_shared/` master and copies
- Does not make the check a hard `lrh validate` gate — warn-don't-block only

## Acceptance Criteria

- `lrh-work-item` and `lrh-implement` each have `references/prior-art-check.md`
  in both `src/lrh/skills/` and `.claude/skills/` with a synced-copy header
- `lrh-work-item` SKILL.md Step 3 explicitly covers code/library duplication
  and records the verdict in the WI body
- `lrh-implement` SKILL.md has a Step 1.5 for prior-art check (warn-don't-block)
- `diff -r src/lrh/skills/lrh-work-item/ .claude/skills/lrh-work-item/` reports no differences
- `diff -r src/lrh/skills/lrh-implement/ .claude/skills/lrh-implement/` reports no differences
- `lrh validate` reports 0 errors

## Validation

- `lrh validate`
