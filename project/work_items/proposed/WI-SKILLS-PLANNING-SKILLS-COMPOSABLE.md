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

## Objective

`/lrh-work-item` was made composable in `WI-SKILLS-LRH-WORK-ITEM-COMPOSABLE`
(PR #331): `disable-model-invocation: true` was removed and replaced with a
`when_to_use` field naming `/lrh-design`, `/lrh-proposal`, and `/lrh-workstream`
as orchestrating callers, on the reasoning that the Step 4 confirm-before-write
gate — not the invocation flag — is the actual write protection (OWASP LLM08).
`/lrh-proposal` and `/lrh-workstream` were left out of that change and still
carry the flag, which blocks a session (or an orchestrating skill) from
delegating proposal/workstream creation the same way it can already delegate
work-item creation. This WI closes that gap by applying the identical
treatment to both remaining planning skills.

## Scope

Apply the `WI-SKILLS-LRH-WORK-ITEM-COMPOSABLE` pattern to:

- `src/lrh/skills/lrh-proposal/SKILL.md` — remove
  `disable-model-invocation: true`; add a `when_to_use` field restricting
  auto-trigger to explicit "create a new design proposal" contexts and naming
  `/lrh-design` as a plausible orchestrating caller.
- `src/lrh/skills/lrh-workstream/SKILL.md` — remove
  `disable-model-invocation: true`; add a `when_to_use` field restricting
  auto-trigger to explicit "create a new workstream" contexts and naming
  `/lrh-design` and `/lrh-proposal` as plausible orchestrating callers.
- Add an "Orchestration" note to each skill's reference material (mirroring
  `lrh-work-item-workflow.md`'s precedent) explaining which skills may invoke
  it and why Step 4 ("User confirms") is sufficient write protection.
- Mirror both skills' edits to `.claude/skills/`.

The Step 4 confirm-before-write gate in both skills is unchanged — this WI
only removes the auto-trigger suppression, not any write protection.

## Non-Goals

- Does not wire `/lrh-design` (or any other skill) to actually *call*
  `/lrh-proposal` or `/lrh-workstream` — this WI only removes the block on
  invocation; orchestration logic in a calling skill is separate follow-on
  work.
- Does not touch `disable-model-invocation` on any execution-phase skill
  (`/lrh-implement`, `/lrh-review-response`, `/lrh-closeout`,
  `/lrh-confirm-fixes`, `/lrh-readiness`) — those create branches, commits,
  and PRs, a materially higher bar than a gated planning-artifact write, and
  keep the flag per `PROP-LRH-PROJECT-LOCAL-SKILLS`.

## Acceptance

- `src/lrh/skills/lrh-proposal/SKILL.md` has no `disable-model-invocation`
  field
- `src/lrh/skills/lrh-proposal/SKILL.md` has a `when_to_use` field restricting
  auto-trigger to explicit proposal-creation contexts
- `src/lrh/skills/lrh-workstream/SKILL.md` has no `disable-model-invocation`
  field
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
