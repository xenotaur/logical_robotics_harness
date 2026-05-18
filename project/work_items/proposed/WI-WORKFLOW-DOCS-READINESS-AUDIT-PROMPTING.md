---
resolution: null
blocked_reason: null
blocked: false
id: WI-WORKFLOW-DOCS-READINESS-AUDIT-PROMPTING
title: Document readiness, audit, prompting, and reporting workflow
type: deliverable
status: proposed
priority: medium
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
  - WI-REQUEST-READY-WORK-ITEM-MVP
blocked_by: []
expected_actions:
  - edit_file
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - workflow documentation explains validate, audit, readiness, ready-work-item, prompt-from-work-item, run-packet-from-work-item, and run-report-from-work-item
  - docs preserve deterministic, assistive, and human-reviewed boundaries
  - examples show valid-but-not-ready and ready/promptable work items
  - documentation does not imply automatic mutation or closeout
  - execution record captures this prompt-driven documentation run
required_evidence:
  - manual_review
artifacts_expected:
  - documentation
---

## Summary

Update user-facing workflow documentation after the readiness CLI and ready-work-item request exist,
so users can move from capture through validation, audit, readiness, prompting, execution, reporting,
and closeout.

## Problem / Context

The design note defines the boundary, but users will need practical workflow documentation once the
new command surfaces are implemented. Documentation should keep deterministic checks, assistive
request generation, and human-reviewed lifecycle decisions separate.

## Scope

- Update relevant workflow, assist, and CLI documentation for the readiness path.
- Include examples of valid-but-not-ready and ready/promptable work items.
- Explain how run reports support evidence-backed closeout without becoming evidence by themselves.
- Cross-link the design note and command references.

## Required Changes

- Add concise workflow documentation for `validate -> audit -> readiness -> ready/refine -> prompt -> execute -> report`.
- Document the boundaries of `lrh work-items readiness`, `lrh request ready-work-item`,
  `lrh request prompt-from-work-item`, and `lrh request run-report-from-work-item`.
- Update README/reference pages affected by the implemented command surfaces.

## Non-Goals

- Do not implement CLI or request behavior in this documentation follow-up.
- Do not claim automatic work-item mutation, branch creation, execution, PR merge, or closeout.
- Do not resolve specific packaging or installability work items.

## Acceptance Criteria

- user-facing docs explain the full readiness/audit/prompting/reporting workflow
- deterministic, assistive, and human-reviewed steps are clearly separated
- examples cover both valid-but-not-ready and promptable items
- command docs align with implemented behavior

## Validation

- `scripts/version tools`
- `scripts/test`
- `scripts/lint`
- `scripts/format --check`
- `lrh work-items validate`
- `lrh work-items audit --format md`
- `lrh work-items readiness --status proposed --format md`
- `lrh validate`
