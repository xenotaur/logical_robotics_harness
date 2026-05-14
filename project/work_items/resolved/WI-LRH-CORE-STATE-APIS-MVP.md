---
resolution: Implemented by the shared read-only core-state API, validation summary, planning relationships, active leaf summaries, evidence links, prompt inputs, and unit coverage recorded in project/executions/WI-LRH-CORE-STATE-APIS-MVP/2026_05_14_00_16_48_IMPLEMENT_CORE_STATE_APIS_MVP.md.
blocked_reason: null
blocked: false
id: WI-LRH-CORE-STATE-APIS-MVP
title: Define shared core state APIs for CLI and serve surfaces
type: deliverable
status: resolved
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
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - shared state API scope is documented for validate, snapshot, request, serve, and future run dry-run consumers
  - API boundaries preserve source Markdown/frontmatter versus typed runtime object separation
  - active focus, workstreams, work items, parent/child relationships, active leaf state, readiness/status summaries, evidence, and status inputs are identified for reuse
  - implementation remains safe-default and does not add autonomous dispatch, branch mutation, PR creation, or fix loops
required_evidence:
  - manual_review
artifacts_expected:
  - documentation
---

## Summary

Define the shared core state and interpretation APIs that `lrh validate`, `lrh snapshot`,
`lrh request`, the safe-default `lrh serve` surface, and future `lrh run --dry-run` should consume.

## Problem / Context

The safe-default execution-framework sequence depends on one reusable interpretation of project
state before the `lrh serve` viewer/prompt workbench is implemented. Without a trackable work item,
this prerequisite cannot be requested, validated, or attached to evidence like the rest of the first
implementation package.

## Required Changes

- Define the state API surfaces needed to load and summarize project identity, validation status,
  current focus, active workstreams, active work items, parent/child relationships, active leaf state,
  readiness/status summaries, evidence/status links, and prompt rendering inputs.
- Include a shared planning relationship/index model so `lrh snapshot`, `lrh serve`, request
  templates, and future run/dry-run surfaces do not each infer workstream/work-item trees separately.
- Preserve the boundary between human-readable source Markdown/frontmatter under `project/` and typed
  runtime objects under `src/lrh/`.
- Identify which existing CLI commands already provide reusable behavior and which gaps must be
  filled before `lrh serve` consumes the same state.
- Keep the API contract safe-default and read/interpretation-oriented; later explicit-click writes
  and run artifacts should build on this state rather than bypass it.

## Non-Goals

- Do not implement `lrh serve`, `lrh run`, autonomous agent dispatch, branch mutation, automatic PR
  creation, CI-fix loops, review-response loops, merge, publish/release, or destructive actions.
- Do not replace the existing project loader, validator, snapshot, or request behavior with a broad
  refactor unless a later implementation prompt explicitly scopes that work.
- Do not force package-split churn before concrete implementation pressure exists.

## Acceptance Criteria

- shared state API scope is documented for validate, snapshot, request, serve, and future run dry-run
  consumers
- API boundaries preserve source Markdown/frontmatter versus typed runtime object separation
- active focus, workstreams, work items, parent/child relationships, active leaf state,
  readiness/status summaries, evidence, and status inputs are identified for reuse
- implementation remains safe-default and does not add autonomous dispatch, branch mutation, PR
  creation, or fix loops

## Validation Commands

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test` when the implementation change touches package behavior or validation logic
- `lrh validate`

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-EXECUTION-FRAMEWORK.md`
- Canonical execution framework design: `project/design/execution_framework_mvp.md`
- Adopted safe-default agentic packaging proposal:
  `project/design/proposals/adopted/safe-default-agentic-extra-packaging/00_proposal.md`

## Risk Notes

- A serve implementation could duplicate snapshot/request logic unless this prerequisite defines the
  shared state boundary first.
- A state API could become too broad if it tries to solve orchestration or agentic execution before
  the safe-default viewer needs it.

## Dependencies / Order

Before `WI-LRH-SERVE-SAFE-DEFAULT-MVP`; before run-state UI, observation adapters, or optional
agentic dispatch adapters.
