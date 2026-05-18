---
resolution: null
blocked_reason: null
blocked: false
id: WI-WORK-ITEM-READINESS-DESIGN
title: Align design for work-item readiness workflow
type: deliverable
status: proposed
priority: high
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
  - project/design/work_item_readiness_workflow.md
depends_on:
  - WI-WORK-ITEM-LIFECYCLE-AUDIT-MVP
blocked_by: []
expected_actions:
  - edit_file
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - readiness lifecycle vocabulary is documented
  - validation, audit, readiness, prompting, and reporting command boundaries are distinguished
  - WI-ASSIST-INSTALLABILITY-HARDENING is captured as a dogfood motivation without being resolved
  - follow-up work items exist for readiness CLI, ready-work-item request, and workflow docs
required_evidence:
  - manual_review
artifacts_expected:
  - documentation
  - work_item_updates
---

## Summary

Align LRH design documentation around the gap between a structurally valid work item and a work item
that is ready to render as an implementation prompt.

## Problem / Context

Dogfooding showed that `WI-ASSIST-INSTALLABILITY-HARDENING` is valid project-control data, but is too
thin for `lrh request prompt-from-work-item` because it lacks execution-facing body sections such as
`Scope`, `Required Changes`, and `Validation`. The design plane needs explicit vocabulary before
implementation PRs add readiness diagnosis or assistive readying commands.

## Scope

- Add or update design documentation for work-item readiness lifecycle terms.
- Document the command split between deterministic validation/audit/readiness and assistive request
  generation.
- Preserve the rule that `lrh work-items validate` should not fail thin proposed items merely because
  they are not implementation-ready.
- Create proposed follow-up implementation work items for the readiness CLI, readying request, and
  workflow documentation.

## Required Changes

- Define valid, audited, ready, promptable, prompted, executed, and evidence-reported work-item
  states in a design note.
- Capture `WI-ASSIST-INSTALLABILITY-HARDENING` as the motivating dogfood case.
- Add concise README/design-index references so reviewers can find the design note.
- Add or update follow-up work items without implementing CLI behavior.

## Non-Goals

- Do not implement `lrh request ready-work-item`.
- Do not implement `lrh work-items readiness`.
- Do not change `prompt-from-work-item` readiness gates.
- Do not automatically mutate work-item Markdown.
- Do not resolve `WI-ASSIST-INSTALLABILITY-HARDENING`.

## Acceptance Criteria

- design documentation distinguishes valid, audited, ready, promptable, implementation-prompted, and
  evidence-reported work items
- deterministic and assistive command boundaries are documented
- `WI-ASSIST-INSTALLABILITY-HARDENING` is recorded as structurally valid but not prompt-ready
- follow-up work items exist for the planned implementation slices

## Validation

- `scripts/version tools`
- `scripts/test`
- `scripts/lint`
- `scripts/format --check`
- `lrh work-items validate`
- `lrh work-items audit --format md`
- `lrh validate`
