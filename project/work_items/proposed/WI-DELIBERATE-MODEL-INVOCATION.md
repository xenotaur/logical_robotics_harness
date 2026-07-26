---
resolution: null
blocked_reason: null
blocked: false
id: WI-DELIBERATE-MODEL-INVOCATION
title: Formalize deliberate model invocation and chain-runner record hygiene
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-EXECUTION-FRAMEWORK
related_design:
  - project/design/proposals/adopted/safe-default-agentic-extra-packaging/00_proposal.md
  - project/design/proposals/proposed/workstream-execution-framework/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
  - promote_reference_skills
acceptance:
  - flag-vs-guidance enforcement of "no chain starts itself" is decided and recorded
  - chain-runner invocation mechanics (invoke flagged links vs. inline) are decided
  - CHAIN-NOTE placement is resolved against the immutable-narrative rule
  - find-or-backfill is normalized in the lifecycle guidance
  - each skill's disable-model-invocation setting and when-to-use guidance is reviewed
required_evidence:
  - manual_review
artifacts_expected:
  - documentation
---

## Summary

Resolve the chain-runner mechanics that `DEC-DELIBERATE-CHAIN-INITIATION`
deferred: where the "no chain starts itself" guarantee is enforced, how a chain
runner invokes lifecycle links, where a run's `CHAIN-NOTE` lives without
violating record immutability, and how record-less PRs are handled — then
cascade the resolutions into skill guidance.

## Problem / Context

`DEC-DELIBERATE-CHAIN-INITIATION` (PR #417) permitted human-initiated chains but
left three mechanics open, all surfaced while dogfooding Taurcode `:land` on that
very PR:

1. **`disable-model-invocation` is a blunt instrument** — it blocks both
   implicit auto-chaining (unwanted) and human-initiated chaining (now wanted).
   Observed cross-repo inconsistency: a chain runner invokes lifecycle subskills
   where they lack the flag and stalls where they carry it (currently
   `lrh-work-item`/`proposal`/`workstream` lack it; the execution/lifecycle
   skills carry it).
2. **`CHAIN-NOTE` vs. immutable narrative** — appending a `CHAIN-NOTE` to an
   existing record's `# Result` at land time conflicts with
   `project/executions/README.md`'s rule that narrative bodies are immutable.
3. **find-or-backfill** — a PR authored outside the skill chain can reach merge
   with no record; the runner must find the review-round record or create an
   honest post-hoc backfill, never rewriting a narrative.

*Prior-art check.* Duplication: none — `WI-SKILLS-PLANNING-SKILLS-COMPOSABLE`
(made planning skills model-invocable) and `WI-SKILLS-NEXT-STEP-CHAIN` (the
lifecycle chain) are related but do not cover these mechanics. Demand:
established — `DEC-DELIBERATE-CHAIN-INITIATION`'s Consequences explicitly defers
this work.

## Scope

Decide and document the three mechanics above and cascade them into
`src/lrh/skills/_shared/lifecycle-chain.md`, affected skills'
`disable-model-invocation` settings and when-to-use guidance, and
`project/executions/README.md` (CHAIN-NOTE placement). Record the resolution in
the decision tier.

## Required Changes

- Decide where "no chain starts itself" is enforced (flag vs. skill-body
  guidance + the deliberate-initiation contract) and do a per-skill
  `disable-model-invocation` pass.
- Decide whether a chain runner may invoke flagged links or must inline their
  workflows; document the invocation contract.
- Resolve the `CHAIN-NOTE` home (a fresh closeout/review record's original body
  vs. a frontmatter field — noting `WI-EXEC-SESSIONS-SCHEMA` frontmatter
  validation may reject arbitrary keys).
- Normalize find-or-backfill in the lifecycle guidance and confirm it never
  rewrites an existing record's narrative.
- Cascade all resolutions into the affected guidance and record the decision.

## Non-Goals

- Do not promote `/lrh-execute` / `/lrh-land` skills (downstream, after this
  lands).
- Do not implement agentic runtime or any LRH-run execution loop.
- Do not edit Taurcode prompts here (separate repo; a handoff prompt already
  covers `:land`/`:execute`).

## Acceptance Criteria

- flag-vs-guidance enforcement of "no chain starts itself" is decided and
  recorded
- chain-runner invocation mechanics (invoke flagged links vs. inline) are
  decided
- CHAIN-NOTE placement is resolved against the immutable-narrative rule
- find-or-backfill is normalized in the lifecycle guidance
- each skill's disable-model-invocation setting and when-to-use guidance is
  reviewed

## Validation

- `lrh validate`
- `lrh work-items validate`
- `scripts/test` when the change touches package behavior or validation logic
- `diff -r src/lrh/skills/ .claude/skills/` when skill files are edited

## Related Workstream and Designs

- Decision: `project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md`
- Workstream: `project/workstreams/proposed/WS-EXECUTION-FRAMEWORK.md` (feeds
  `WI-BOUNDED-STABILIZATION-LOOP-DESIGN`)
- `project/executions/README.md`; `src/lrh/skills/_shared/lifecycle-chain.md`;
  `PROP-SAFE-DEFAULT-AGENTIC-EXTRA-PACKAGING`

## Risk Notes

- Relaxing the flag could reopen implicit auto-chaining unless enforcement
  genuinely moves to guidance + the deliberate-initiation contract.
- The frontmatter route for `CHAIN-NOTE` may collide with the new
  execution-record validation.

## Dependencies / Order

- After `DEC-DELIBERATE-CHAIN-INITIATION` (merged). Feeds
  `WI-BOUNDED-STABILIZATION-LOOP-DESIGN`; unblocks promoting `/lrh-execute` and
  `/lrh-land` as reference implementations.
