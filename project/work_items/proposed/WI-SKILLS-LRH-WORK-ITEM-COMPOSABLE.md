---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-LRH-WORK-ITEM-COMPOSABLE
title: Make /lrh-work-item composable by enabling model invocation
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
  - implement_lrh_proposal
  - implement_lrh_workstream
  - implement_lrh_design_step4
acceptance:
  - src/lrh/skills/lrh-work-item/SKILL.md has no disable-model-invocation field
  - src/lrh/skills/lrh-work-item/SKILL.md has a when_to_use field restricting auto-trigger to explicit creation contexts
  - Step 4 confirm gate in SKILL.md body is unchanged
  - lrh-work-item-workflow.md documents the orchestration use case
  - "diff src/lrh/skills/lrh-work-item/SKILL.md .claude/skills/lrh-work-item/SKILL.md reports no differences"
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-work-item/SKILL.md
  - .claude/skills/lrh-work-item/SKILL.md
  - src/lrh/skills/lrh-work-item/references/lrh-work-item-workflow.md
  - .claude/skills/lrh-work-item/references/lrh-work-item-workflow.md
---

## Summary

Remove `disable-model-invocation: true` from `/lrh-work-item` and replace it
with a tight `when_to_use` field, enabling orchestrating skills (`/lrh-design`,
`/lrh-proposal`, `/lrh-workstream`) to invoke `/lrh-work-item` as a sub-task
while preserving the Step 4 confirm gate as the sole write protection for the
control plane.

## Problem / Context

`disable-model-invocation: true` conflates two concerns: preventing accidental
keyword auto-triggering and blocking explicit model invocation via the Skill
tool. The first is desirable; the second prevents skill composition. Skills
such as `/lrh-design` Step 4, `/lrh-proposal`, and `/lrh-workstream` need to
call `/lrh-work-item` as a sub-task without requiring the user to manually
type the slash command. The Step 4 confirm gate — which shows the complete
proposed work item and requires explicit user approval before any file is
written — is sufficient as the write protection, consistent with OWASP LLM08
guidance ("Require human approval for high-impact actions").

## Scope

- Edit `src/lrh/skills/lrh-work-item/SKILL.md` frontmatter only
- Add orchestration documentation to `lrh-work-item-workflow.md`
- Mirror both edits to `.claude/skills/lrh-work-item/`

## Required Changes

1. Edit `src/lrh/skills/lrh-work-item/SKILL.md` frontmatter:
   - Remove the `disable-model-invocation: true` line.
   - Add a `when_to_use` field:
     ```
     when_to_use: >
       Invoke only when explicitly creating a new LRH work item planning
       artifact in project/work_items/proposed/. Do not invoke when the user
       is discussing, reading, or querying work items. Suitable for
       orchestration from /lrh-design, /lrh-proposal, or /lrh-workstream
       when those skills need to create companion work items as part of a
       design-capture workflow.
     ```
2. Mirror the same frontmatter edit to `.claude/skills/lrh-work-item/SKILL.md`.
3. Edit `src/lrh/skills/lrh-work-item/references/lrh-work-item-workflow.md`:
   - Add a section documenting the orchestration use case: which skills may
     invoke `/lrh-work-item`, how the confirm gate protects the control plane
     in that context, and the OWASP LLM08 rationale for relying on the gate
     rather than `disable-model-invocation`.
4. Mirror the same edit to `.claude/skills/lrh-work-item/references/lrh-work-item-workflow.md`.

## Non-Goals

- Do not change the Step 4 confirm gate or any execution step in SKILL.md.
- Do not implement `/lrh-proposal`, `/lrh-workstream`, or the `/lrh-design`
  Step 4 update — those are separate work items.
- Do not modify the work item schema, validator, or any other skill.
- Do not add `user-invocable: false` — `/lrh-work-item` should remain
  directly invocable by the user.

## Acceptance Criteria

- `src/lrh/skills/lrh-work-item/SKILL.md` has no `disable-model-invocation`
  field (removed, not set to `false`)
- `src/lrh/skills/lrh-work-item/SKILL.md` has a `when_to_use` field with
  language restricting auto-trigger to explicit work item creation and naming
  the orchestrating skills
- The Step 4 confirm gate text in SKILL.md body is unchanged
- `lrh-work-item-workflow.md` has a new orchestration section
- `diff src/lrh/skills/lrh-work-item/SKILL.md .claude/skills/lrh-work-item/SKILL.md`
  reports no differences
- `diff src/lrh/skills/lrh-work-item/references/lrh-work-item-workflow.md \`
  `.claude/skills/lrh-work-item/references/lrh-work-item-workflow.md`
  reports no differences
- `lrh validate` reports 0 errors

## Validation

- `scripts/version tools`
- `lrh validate`
- `diff src/lrh/skills/lrh-work-item/SKILL.md .claude/skills/lrh-work-item/SKILL.md`
- `diff src/lrh/skills/lrh-work-item/references/lrh-work-item-workflow.md .claude/skills/lrh-work-item/references/lrh-work-item-workflow.md`

## Risk Notes

- Removing `disable-model-invocation` also allows the skill to be preloaded
  into forked subagents (`context: fork`). This is low-risk because the
  confirm gate fires in any context, but it should be noted in the workflow
  doc so future skill authors understand the trade-off.
- The `when_to_use` field narrows auto-trigger surface but cannot fully
  prevent keyword matching; the confirm gate remains the last line of defence.
