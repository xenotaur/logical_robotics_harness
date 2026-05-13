---
resolution: null
blocked_reason: null
blocked: false
id: WI-LRH-SERVE-SAFE-DEFAULT-MVP
title: Define safe-default lrh serve viewer and prompt workbench MVP
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
  - project/design/execution_framework_mvp.md
  - project/design/proposals/adopted/safe-default-agentic-extra-packaging/00_proposal.md
depends_on:
  - WI-LRH-CORE-STATE-APIS-MVP
  - WI-WORKSTREAM-PLANNING-TREE-RELATIONSHIPS-MVP
  - WI-PLANNING-TREE-VALIDATION-RULES-MVP
  - WI-WORKSTREAM-SNAPSHOT-MVP
blocked_by: []
expected_actions:
  - edit_file
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - safe-default serve scope is implemented or documented as a local viewer and prompt workbench
  - serve consumes shared snapshot planning summaries and control-plane state APIs rather than inventing a workflow engine or tree interpreter
  - default writes are read-only or explicit-click LRH control-artifact writes only
  - autonomous dispatch, branch mutation, PR creation, CI-fix loops, review-fix loops, merge, and publish remain out of scope
required_evidence:
  - manual_review
artifacts_expected:
  - documentation
---

## Summary

Define and later implement the first safe-default `lrh serve` MVP as a local project-state viewer and
prompt workbench, not an autonomous runner.

## Problem / Context

The execution-framework plan now prioritizes making the manual Huge Loop visible and easier to
operate before adding durable run state, observation adapters, or optional agentic automation.
`lrh serve` should project the same control-plane state used by commands such as `lrh validate`,
`lrh snapshot`, and `lrh request`.

## Required Changes

- Define or implement a read-only local server skeleton that shows project identity, validation
  status, current focus, active workstreams, active work items, shared planning-tree/snapshot summary,
  and available next human actions.
- Add a prompt workbench path for generated prompts with editable preview, copy/download fallback,
  and a safe-default "Generate run packet" action that renders a request artifact without executing,
  simulating, dispatching, observing, mutating, or stabilizing anything.
- Preserve a strict write boundary: no default write unless a human explicitly clicks to create or
  update LRH control artifacts such as prompt packets, manual run state, evidence, report drafts, or
  execution records.
- Use conservative local server defaults such as binding to `127.0.0.1`, avoiding permissive CORS,
  not displaying secrets, and not browsing outside the project root.

## Non-Goals

- Do not dispatch agents, mutate branches, push commits, open PRs automatically, run CI-fix loops,
  run review-response loops, merge, publish/release, or perform destructive actions.
- Do not treat `lrh serve` as a sandbox, as a separate workflow engine, or as the first place that
  planning-tree relationships are interpreted.
- Do not force broad package-layout churn before concrete implementation pressure exists.

## Acceptance Criteria

- safe-default serve scope is implemented or documented as a local viewer and prompt workbench
- serve consumes shared snapshot planning summaries and control-plane state APIs rather than inventing
  a workflow engine or tree interpreter
- default writes are read-only or explicit-click LRH control-artifact writes only
- autonomous dispatch, branch mutation, PR creation, CI-fix loops, review-fix loops, merge, and
  publish remain out of scope

## Validation Commands

- `scripts/version tools`
- `lrh validate`
- `scripts/test` when the implementation change touches package behavior or validation logic

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-EXECUTION-FRAMEWORK.md`
- Canonical execution framework design: `project/design/execution_framework_mvp.md`
- Adopted safe-default agentic packaging proposal:
  `project/design/proposals/adopted/safe-default-agentic-extra-packaging/00_proposal.md`

## Risk Notes

- A local server could be mistaken for an autonomous runner unless the default capability boundary is
  explicit.
- A local server could be mistaken for a sandbox unless documentation explains that it is a local
  assist UI with conservative defaults, not an isolation boundary.
- Write conveniences could accidentally broaden into mutation-capable workflow automation.

## Dependencies / Order

After design/control-plane alignment, `WI-LRH-CORE-STATE-APIS-MVP`, planning relationship
validation, and `WI-WORKSTREAM-SNAPSHOT-MVP`. Before execution-readiness schema work that depends on
serve sequencing, run-state UI, observation adapters, or optional agentic dispatch adapters.
