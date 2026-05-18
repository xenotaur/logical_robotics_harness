---
resolution: null
blocked_reason: null
blocked: false
id: WI-WORK-ITEMS-READINESS-CLI-MVP
title: Add deterministic work-item readiness diagnostics CLI
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
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - lrh work-items readiness reports missing prompt-readiness sections for selected work items
  - readiness diagnostics are deterministic and non-mutating
  - validate behavior remains limited to structural work-item hygiene
  - tests cover ready and not-ready work-item examples
required_evidence:
  - test_result
  - manual_review
artifacts_expected:
  - code_diff
  - documentation
---

## Summary

Implement the deterministic `lrh work-items readiness` MVP that diagnoses whether selected work items
have the execution-facing sections needed for implementation prompting.

## Problem / Context

LRH can validate thin proposed work items as project-control records, but users need a deterministic
way to see why a selected item is not ready for `prompt-from-work-item`. The readiness command should
make the missing-section boundary visible without changing validation semantics.

## Scope

- Add a `lrh work-items readiness` command for deterministic prompt-readiness diagnostics.
- Reuse or align with the existing `prompt-from-work-item` readiness checks where practical.
- Report missing sections and promptability blockers in a stable human-readable format, with a JSON
  format only if that remains narrow and useful.
- Include tests for valid-but-not-ready items and prompt-ready items.

## Required Changes

- Add CLI plumbing under the existing work-items command group.
- Add a small readiness diagnostic module or shared helper if needed.
- Document the command in the relevant README/reference surface.
- Preserve `lrh work-items validate` behavior for thin proposed work items.

## Non-Goals

- Do not generate rewritten work-item content.
- Do not implement `lrh request ready-work-item`.
- Do not dispatch agents, run implementation work, mutate branches, or close work items.
- Do not resolve `WI-ASSIST-INSTALLABILITY-HARDENING`.

## Acceptance Criteria

- `lrh work-items readiness` reports missing `Scope`, `Required Changes`, `Acceptance Criteria`, or
  `Validation` details when a selected item lacks them
- readiness diagnostics are deterministic and non-mutating
- unit tests cover pass and fail cases
- validation/audit behavior remains unchanged except for any explicitly documented shared helper

## Validation

- `scripts/version tools`
- `scripts/test`
- `scripts/lint`
- `scripts/format --check`
- `lrh work-items validate`
- `lrh validate`
