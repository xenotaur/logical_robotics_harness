---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-PLANNING-SKILLS-COMPOSABLE
title: Make /lrh-proposal and /lrh-workstream composable by enabling model invocation
type: operation
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design:
  - project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - implement_lrh_design_orchestration
  - modify_execution_skill_invocation_flags
acceptance:
  - src/lrh/skills/lrh-proposal/SKILL.md has no disable-model-invocation field
  - src/lrh/skills/lrh-proposal/SKILL.md has a when_to_use field restricting auto-trigger to explicit proposal-creation contexts
  - src/lrh/skills/lrh-workstream/SKILL.md has no disable-model-invocation field
  - src/lrh/skills/lrh-workstream/SKILL.md has a when_to_use field restricting auto-trigger to explicit workstream-creation contexts
  - "Step 4 (User confirms) in both SKILL.md bodies is unchanged"
  - lrh-proposal's references document the orchestration use case (which skills may invoke it, why the Step 4 confirm gate is sufficient write protection)
  - lrh-workstream's references document the orchestration use case (which skills may invoke it, why the Step 4 confirm gate is sufficient write protection)
  - diff -r src/lrh/skills/lrh-proposal/ .claude/skills/lrh-proposal/ reports no differences
  - diff -r src/lrh/skills/lrh-workstream/ .claude/skills/lrh-workstream/ reports no differences
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-proposal/SKILL.md
  - src/lrh/skills/lrh-proposal/references/proposal-body-guide.md
  - .claude/skills/lrh-proposal/SKILL.md
  - .claude/skills/lrh-proposal/references/proposal-body-guide.md
  - src/lrh/skills/lrh-workstream/SKILL.md
  - src/lrh/skills/lrh-workstream/references/workstream-body-guide.md
  - .claude/skills/lrh-workstream/SKILL.md
  - .claude/skills/lrh-workstream/references/workstream-body-guide.md
---

# Make `/lrh-proposal` and `/lrh-workstream` composable by enabling model invocation

## Summary

Remove `disable-model-invocation: true` from `/lrh-proposal` and
`/lrh-workstream` and replace each with a tight `when_to_use` field, extending
the composability already granted to `/lrh-work-item`
(`WI-SKILLS-LRH-WORK-ITEM-COMPOSABLE`, PR #331) so orchestrating skills (e.g.
`/lrh-design`) can invoke them as sub-tasks while the Step 4 confirm gate
remains the sole write protection for the control plane.

## Problem / Context

`disable-model-invocation: true` conflates two concerns: preventing accidental
keyword auto-triggering and blocking explicit model invocation via the Skill
tool. `/lrh-work-item` already resolved this tension by removing the flag and
relying on its Step 4 confirm gate instead, consistent with OWASP LLM08
("Require human approval for high-impact actions"). `/lrh-proposal` and
`/lrh-workstream` were left out of that change, so a design-discussion session
(or an orchestrating skill like `/lrh-design`) cannot delegate proposal or
workstream creation the same way it can already delegate work-item creation —
the exact friction hit while capturing `PROP-LRH-CONFIRM-FIXES` and
`WS-SKILLS-CONFIRM-FIXES` directly in a prior session, since both skills had
to be written by hand instead of invoked.

## Scope

- Edit `src/lrh/skills/lrh-proposal/SKILL.md` frontmatter only
- Edit `src/lrh/skills/lrh-workstream/SKILL.md` frontmatter only
- Add orchestration documentation to each skill's reference material
- Mirror all edits to `.claude/skills/`

## Required Changes

1. Edit `src/lrh/skills/lrh-proposal/SKILL.md` frontmatter:
   - Remove the `disable-model-invocation: true` line.
   - Add a `when_to_use` field restricting auto-trigger to explicit
     "create a new design proposal" contexts and naming `/lrh-design` as a
     plausible orchestrating caller.
2. Mirror the same frontmatter edit to `.claude/skills/lrh-proposal/SKILL.md`.
3. Edit `src/lrh/skills/lrh-workstream/SKILL.md` frontmatter:
   - Remove the `disable-model-invocation: true` line.
   - Add a `when_to_use` field restricting auto-trigger to explicit
     "create a new workstream" contexts and naming `/lrh-design` and
     `/lrh-proposal` as plausible orchestrating callers.
4. Mirror the same frontmatter edit to `.claude/skills/lrh-workstream/SKILL.md`.
5. Add an "Orchestration" section to `src/lrh/skills/lrh-proposal/references/`
   (mirroring `lrh-work-item-workflow.md`'s precedent section) documenting
   which skills may invoke `/lrh-proposal` and why the Step 4 confirm gate is
   sufficient write protection.
6. Mirror the same reference edit to `.claude/skills/lrh-proposal/references/`.
7. Add the equivalent "Orchestration" section to
   `src/lrh/skills/lrh-workstream/references/`.
8. Mirror the same reference edit to `.claude/skills/lrh-workstream/references/`.

## Non-Goals

- Do not change the Step 4 confirm gate or any execution step in either
  `SKILL.md`.
- Do not wire `/lrh-design` (or any other skill) to actually *call*
  `/lrh-proposal` or `/lrh-workstream` — this WI only removes the block on
  invocation; orchestration logic in a calling skill is separate follow-on
  work.
- Do not touch `disable-model-invocation` on any execution-phase skill
  (`/lrh-implement`, `/lrh-review-response`, `/lrh-closeout`,
  `/lrh-confirm-fixes`, `/lrh-readiness`). The distinguishing factor is **not**
  that those skills create branches, commits, or PRs — `/lrh-work-item`,
  `/lrh-proposal`, and `/lrh-workstream` all do that too (each behind its own
  Step 4 gate, in a brand-new self-contained branch/PR holding only its own
  artifact, trivially abandoned if wrong). It is that execution-phase skills
  act on already-existing shared state: `/lrh-review-response` pushes onto an
  existing open PR, `/lrh-closeout` commits directly to `main`, and
  `/lrh-confirm-fixes` resolves live GitHub review threads. That
  higher-consequence, less-reversible surface keeps the flag; see
  `PROP-LRH-PROJECT-LOCAL-SKILLS`.
- Do not modify the proposal or workstream schema, validator, or any other
  skill.

## Acceptance Criteria

- `src/lrh/skills/lrh-proposal/SKILL.md` has no `disable-model-invocation`
  field (removed, not set to `false`)
- `src/lrh/skills/lrh-proposal/SKILL.md` has a `when_to_use` field restricting
  auto-trigger to explicit proposal-creation contexts
- `src/lrh/skills/lrh-workstream/SKILL.md` has no `disable-model-invocation`
  field (removed, not set to `false`)
- `src/lrh/skills/lrh-workstream/SKILL.md` has a `when_to_use` field
  restricting auto-trigger to explicit workstream-creation contexts
- Step 4 ("User confirms") in both `SKILL.md` bodies is unchanged
- `lrh-proposal`'s references document the orchestration use case (which
  skills may invoke it, why the Step 4 confirm gate is sufficient write
  protection)
- `lrh-workstream`'s references document the orchestration use case (same)
- `diff -r src/lrh/skills/lrh-proposal/ .claude/skills/lrh-proposal/` reports
  no differences
- `diff -r src/lrh/skills/lrh-workstream/ .claude/skills/lrh-workstream/`
  reports no differences
- `lrh validate` reports 0 errors

## Validation

- `scripts/version tools`
- `lrh validate`
- `diff -r src/lrh/skills/lrh-proposal/ .claude/skills/lrh-proposal/`
- `diff -r src/lrh/skills/lrh-workstream/ .claude/skills/lrh-workstream/`

## Risk Notes

- Removing `disable-model-invocation` also allows both skills to be preloaded
  into forked subagents (`context: fork`). Low-risk since the confirm gate
  fires in any context, but worth noting per the `/lrh-work-item` precedent.
- The `when_to_use` field narrows auto-trigger surface but cannot fully
  prevent keyword matching; the confirm gate remains the last line of
  defense.
