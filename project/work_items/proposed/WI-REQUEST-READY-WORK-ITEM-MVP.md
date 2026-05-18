---
resolution: null
blocked_reason: null
blocked: false
id: WI-REQUEST-READY-WORK-ITEM-MVP
title: Add assistive ready-work-item request MVP
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
  - WI-WORK-ITEM-READINESS-DESIGN
  - WI-WORK-ITEMS-READINESS-CLI-MVP
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - lrh request ready-work-item renders a human-reviewable refinement request for a selected work item
  - generated guidance proposes missing execution sections without mutating source files
  - request output preserves cited project context and distinguishes suggestions from accepted source truth
  - tests cover selected work-item resolution and missing-section guidance
required_evidence:
  - test_result
  - manual_review
artifacts_expected:
  - code_diff
  - documentation
---

## Summary

Add an assistive `lrh request ready-work-item` MVP that helps a human refine a valid-but-thin work
item into a prompt-ready work item.

## Problem / Context

A deterministic readiness command can say what is missing, but LRH also needs an assistive request
surface that proposes candidate `Scope`, `Required Changes`, `Acceptance Criteria`, and `Validation`
sections from referenced project context. The request should help humans edit work items; it should
not automatically modify the control-plane source.

## Scope

- Add a canonical `lrh request ready-work-item` request surface.
- Load one selected work item and relevant project context.
- Render a Markdown request that asks an assistant to propose missing readiness sections for human
  review.
- Clearly mark the output as suggested edits, not accepted source truth.

## Required Changes

- Add request command/template or structured renderer support for `ready-work-item`.
- Reuse readiness diagnostics from `lrh work-items readiness` when available.
- Document the request command and its non-mutating behavior.
- Add tests for command discovery, rendering, and missing-section guidance.

## Non-Goals

- Do not automatically write changes back to the selected work-item file.
- Do not render a direct implementation prompt; that remains `prompt-from-work-item`.
- Do not run validation commands, dispatch agents, create branches, or close work items.
- Do not resolve `WI-ASSIST-INSTALLABILITY-HARDENING`.

## Acceptance Criteria

- `lrh request ready-work-item` renders a reviewable refinement request for a selected item
- the request includes missing readiness diagnostics and relevant source context
- generated output distinguishes proposed content from accepted work-item source
- tests cover command behavior and no automatic mutation occurs

## Validation

- `scripts/version tools`
- `scripts/test`
- `scripts/lint`
- `scripts/format --check`
- `lrh work-items validate`
- `lrh validate`
