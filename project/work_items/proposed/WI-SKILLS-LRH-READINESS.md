---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-LRH-READINESS
title: Implement /lrh-readiness skill to close the ready-work-item apply loop
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design:
  - .claude/skills/lrh-work-item/references/lrh-work-item-workflow.md
  - .claude/skills/lrh-implement/SKILL.md
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - modify_execution_readiness_schema
  - implement_lrh_implement_changes
acceptance:
  - .claude/skills/lrh-readiness/SKILL.md and src/lrh/skills/lrh-readiness/SKILL.md exist and are identical
  - Skill runs lrh work-items readiness <WI-ID>; if already ready, reports and stops without further action
  - "If not ready, skill runs lrh request ready-work-item <WI-ID>, shows the proposal, and applies it only after explicit user confirmation"
  - After applying, skill re-runs lrh work-items readiness to confirm the item now passes, or reports remaining gaps if it does not
  - Demonstrated end-to-end against WI-AGENT-BRANCH-CONTAINMENT (currently prompt_ready:no, blocking:missing Scope section, missing Validation commands)
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-readiness/SKILL.md
  - .claude/skills/lrh-readiness/SKILL.md
---

# WI-SKILLS-LRH-READINESS

## Summary

Implement a `/lrh-readiness` Claude Code skill that closes the loop `lrh
request ready-work-item` currently leaves open: it renders an assistive
refinement proposal for a thin work item but "does not edit files
automatically." This skill checks readiness, gets the proposal, shows it for
confirmation, applies it, and re-validates — matching the confirm-gate →
write → validate pattern every other LRH skill already uses for its own
artifact type.

## Problem / Context

`lrh work-items readiness` is already checked in two places (standalone CLI,
and `/lrh-implement` Step 1), which only warns and lets the user decide
whether to continue — it does not attempt any fix. `lrh request
ready-work-item` renders a refinement proposal but, per its own workflow doc,
does not apply it. No skill currently bridges "here's a proposed fix" to "the
file is fixed and re-validated." Scoped via `/lrh-design` in this
conversation as a small, single-PR skill.

This is a different "readiness" concept from `WI-EXECUTION-READINESS-SCHEMA`
/ `FOCUS-EXECUTION-FRAMEWORK-PLANNING` / `WS-EXECUTION-FRAMEWORK`, which cover
opt-in autonomous-execution metadata (`execution_ready`, `autonomy_level`,
etc. in `src/lrh/control/execution_readiness.py`). This work item is scoped
only to prompt-readiness of a work item's body sections.

## Scope

- Implement `src/lrh/skills/lrh-readiness/SKILL.md` and mirror to
  `.claude/skills/lrh-readiness/SKILL.md`.
- Wire the skill to the existing `lrh work-items readiness` and
  `lrh request ready-work-item` CLI commands — no new CLI surface.

## Required Changes

1. Create `src/lrh/skills/lrh-readiness/SKILL.md` following the LRH skill
   pattern: interview-free (single `WI-*` ID argument), run readiness check,
   run `ready-work-item` if needed, confirm gate, apply patch, re-validate,
   commit.
2. Mirror to `.claude/skills/lrh-readiness/SKILL.md`.
3. Add a `## Skills` entry to `CLAUDE.md`.

## Non-Goals

- Do not change `/lrh-implement`'s Step 1 behavior — it still warns and does
  not hard-block; this skill is an optional prerequisite step, not a
  replacement.
- Do not touch the execution-readiness schema
  (`src/lrh/control/execution_readiness.py`) — unrelated concept.
- Do not batch-process multiple work items in one invocation.
- Do not apply any patch without an explicit confirmation gate.

## Acceptance Criteria

- `src/lrh/skills/lrh-readiness/SKILL.md` and `.claude/skills/lrh-readiness/SKILL.md` exist and are identical (`diff -r`).
- Given a ready `WI-*`, the skill reports readiness and takes no further action.
- Given a not-ready `WI-*` (e.g. `WI-AGENT-BRANCH-CONTAINMENT`), the skill renders the `ready-work-item` proposal, shows it, and only writes after confirmation.
- After applying, `lrh work-items readiness <WI-ID>` reports `prompt_ready: yes`, or the skill reports which gaps remain.
- `lrh validate` reports 0 errors.

## Validation

- `lrh validate`
- `diff -r src/lrh/skills/lrh-readiness/ .claude/skills/lrh-readiness/`
- `lrh work-items readiness WI-AGENT-BRANCH-CONTAINMENT --format md`

## Risk Notes

- Applying a rendered patch automatically risks silently absorbing scope the
  human didn't review carefully — the confirm gate is the only mitigation;
  do not weaken it for convenience.
- `ready-work-item`'s proposal quality depends on the thin item's existing
  content; if the proposal itself is low-quality, the skill should say so
  rather than force it through.

## Related Workstream and Designs

- `.claude/skills/lrh-work-item/references/lrh-work-item-workflow.md`
- `.claude/skills/lrh-implement/SKILL.md`
- No workstream — scoped directly as a standalone work item via `/lrh-design`
