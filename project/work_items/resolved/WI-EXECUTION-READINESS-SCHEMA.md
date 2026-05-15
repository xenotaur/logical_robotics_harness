---
resolution: Implemented by opt-in execution-readiness metadata interpretation, strict selected-leaf validation, documentation, and tests recorded in project/executions/WI-EXECUTION-READINESS-SCHEMA/2026_05_14_21_04_06_IMPLEMENT_EXECUTION_READINESS_SCHEMA.md.
blocked_reason: null
blocked: false
id: WI-EXECUTION-READINESS-SCHEMA
title: Define execution readiness schema for executable leaves
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
  - project/design/proposals/proposed/workstream-execution-framework/00_proposal.md
  - project/design/proposals/adopted/workstreams-and-recursive-planning-tree/00_proposal.md
depends_on:
  - WI-WORK-ITEM-EXECUTION-READY-CONCEPT-MVP
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
  - execution-readiness fields are documented for selected or explicitly opted-in executable leaves
  - readiness explicitly preserves human approval before branch mutation or autonomous execution
  - the documented schema is sufficient input for run-packet dry-run work
  - non-goals defer validation code, branch mutation, and backend implementation
required_evidence:
  - manual_review
artifacts_expected:
  - documentation
---

## Summary

Define the work-item fields required before any selected work item can be used as an executable leaf
for future run-packet generation or `lrh run`-style execution workflows. This is the first item in
the first execution-contract implementation package.

## Problem / Context

The execution-framework workstream needs a contract that distinguishes ordinary planning leaves from leaves ready for bounded execution. Readiness must be explicit, reviewable, and safe-default before any runtime behavior, branch mutation, agent backend, or autonomous loop exists.

## Required Changes

- Document candidate readiness fields such as `autonomy_level`, `operation_risk`, `allowed_paths`, `forbidden_paths`, `validation_commands`, `max_review_rounds`, `max_ci_rounds`, `requires_human_merge`, and `requires_human_closeout`.
- Specify which fields are required for the first dry-run packet contract and which are advisory until validation matures.
- Describe how readiness metadata relates to workstream/work-item planning-tree semantics without making every work item executable by default.
- Keep strict readiness validation opt-in for work items that declare execution/run metadata or are
  passed to a run-packet/run command.
- Update project-control documentation needed for later prompt generation.

## Non-Goals

- Do not implement runtime code, CLI behavior, schema validation, GitHub API integration, agent execution, execution backends, orchestration, or `lrh run` behavior as part of this planning/design item.
- Do not add automatic merge, release/publish automation, privileged workflow execution, MCP bridges, telemetry systems, or full autonomous execution.

## Acceptance Criteria

- execution-readiness fields are documented for selected or explicitly opted-in executable leaves
- readiness explicitly preserves human approval before branch mutation or autonomous execution
- the documented schema is sufficient input for run-packet dry-run work
- non-goals defer validation code, branch mutation, and backend implementation

## Validation Commands

- `scripts/version tools`
- `lrh validate`
- `scripts/test` when the implementation change touches package behavior or validation logic

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-EXECUTION-FRAMEWORK.md`
- Canonical living execution-framework MVP design: `project/design/execution_framework_mvp.md`
- Proposed execution-framework proposal: `project/design/proposals/proposed/workstream-execution-framework/00_proposal.md`
- Adopted planning-tree proposal: `project/design/proposals/adopted/workstreams-and-recursive-planning-tree/00_proposal.md`

## Risk Notes

- Over-scoping readiness into runtime validation before the contract is reviewed.
- Treating all work items as execution-ready by default.
- Applying strict runner-readiness validation broadly enough to break existing planning/control-plane
  work items.

## Dependencies / Order

First in the first execution-contract implementation package, after prerequisite shared state APIs,
planning relationship validation, and snapshot-visible planning summaries are available.
`WI-LRH-SERVE-SAFE-DEFAULT-MVP` is not a prerequisite for this package; serve should later consume
this contract rather than define it. `WI-RUN-PACKET-DRY-RUN` and `WI-RUN-REPORT-MVP` should consume
this contract rather than inventing their own readiness fields.
