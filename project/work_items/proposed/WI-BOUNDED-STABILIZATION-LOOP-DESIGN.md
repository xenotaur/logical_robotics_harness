---
resolution: null
blocked_reason: null
blocked: false
id: WI-BOUNDED-STABILIZATION-LOOP-DESIGN
title: Plan bounded review and CI stabilization loop
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
  - project/design/proposals/proposed/workstream-execution-framework/00_proposal.md
  - project/design/proposals/adopted/workstreams-and-recursive-planning-tree/00_proposal.md
  - src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md
depends_on:
  - WI-GITHUB-PR-CI-OBSERVATION
  - WI-AGENT-BRANCH-CONTAINMENT
  - WI-DELIBERATE-MODEL-INVOCATION
blocked_by: []
expected_actions:
  - edit_file
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - iteration limits and stop conditions are documented
  - escalation and human-review rules are explicit
  - manual, assisted, and bounded-auto modes are distinguished
  - no mutation-capable automation or backend implementation is added
required_evidence:
  - manual_review
artifacts_expected:
  - documentation
---

## Summary

Plan the bounded review/CI response loop, iteration limits, stop conditions, and escalation rules before implementing mutation-capable automation.

## Problem / Context

The execution-framework proposal includes bounded PR/CI stabilization, but automation must not be added until loop limits, evidence rules, escalation paths, and human gates are explicit.

## Required Changes

- Document review and CI iteration limits such as `max_review_rounds` and `max_ci_rounds`.
- Define stop conditions, escalation rules, and requires-human-review outcomes.
- Describe how loop attempts would update run reports and evidence without promising autonomous behavior.
- Separate manual/assisted/bounded-auto modes so manual-mode parity remains available.

## Non-Goals

- Do not implement runtime code, CLI behavior, schema validation, GitHub API integration, agent execution, execution backends, orchestration, or `lrh run` behavior as part of this planning/design item.
- Do not add automatic merge, release/publish automation, privileged workflow execution, MCP bridges, telemetry systems, or full autonomous execution.

## Acceptance Criteria

- iteration limits and stop conditions are documented
- escalation and human-review rules are explicit
- manual, assisted, and bounded-auto modes are distinguished
- no mutation-capable automation or backend implementation is added

## Validation Commands

- `scripts/version tools`
- `lrh validate`
- `scripts/test` when the implementation change touches package behavior or validation logic

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-EXECUTION-FRAMEWORK.md`
- Proposed execution-framework proposal: `project/design/proposals/proposed/workstream-execution-framework/00_proposal.md`
- Adopted planning-tree proposal: `project/design/proposals/adopted/workstreams-and-recursive-planning-tree/00_proposal.md`

## Risk Notes

- A stabilization-loop plan could be interpreted as approval for full autonomous execution.
- Retry loops could obscure failures unless stop conditions are concrete.
- **Evidence this risk is not hypothetical:** `WI-REVIEW-ROUND-ESCALATION-GATE`
  (resolved, PR #445) implemented the *assisted-mode* slice of exactly this
  loop — a durable round cap on `/lrh-confirm-fixes` Step 8's bot-retrigger
  loop — as skill-embedded bash/git prose. It took 8 review rounds to reach
  its current state, each round finding a genuinely different category of
  correctness bug (state-machine/crash-recovery semantics, PR-identity
  atomicity, architectural placement of durable state relative to the
  reviewed branch, cross-platform shell portability, multi-tenant branch
  namespacing, concurrent-write races) — not the same bug rephrased. See
  `src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md`'s own
  "Risk Notes — deferred hardening" section for what remains unresolved
  even after those 8 rounds (untested in practice, guessed retry/staleness
  thresholds, no automated test coverage). Before designing the
  `bounded-auto` mode's own iteration/state tracking (which will likely
  need similar durable round/CI-count state), weigh whether it should
  reuse this same bash-in-skill-prose approach — which the evidence above
  suggests is expensive to get right and inherently untestable — or
  whether round/CI-loop state tracking should become a shared,
  unit-tested LRH primitive (real code, not skill prose) that both the
  assisted and bounded-auto modes draw on.

## Dependencies / Order

After read-only observation design. Implementation should wait until readiness, packet, report, and policy contracts exist.
