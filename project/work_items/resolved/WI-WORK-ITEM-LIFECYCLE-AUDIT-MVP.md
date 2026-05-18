---
resolution: implemented in this PR with deterministic audit command, validation refinements, docs, tests, semantic audit template, and proposed-bucket audit review.
blocked_reason: null
blocked: false
id: WI-WORK-ITEM-LIFECYCLE-AUDIT-MVP
title: Implement work-item lifecycle audit MVP
type: deliverable
status: resolved
priority: high
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_roadmap:
  - ROADMAP-PHASE-03
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_workstreams:
  - WS-EXECUTION-FRAMEWORK
related_design:
  - execution_framework_mvp
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - add_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - work-item lifecycle audit command exists with Markdown and JSON formats
  - deterministic work-item metadata/reference validation is improved without semantic completion judgments
  - current organize, validate, and audit behavior is documented
  - semantic work-item audit assist template exists
  - current proposed bucket is audited conservatively
  - only high-confidence stale work items are resolved and ambiguous items are left proposed
required_evidence:
  - code_diff
  - test_result
  - audit_output
artifacts_expected:
  - src/lrh/work_items/audit.py
  - tests/work_items_tests/audit_test.py
  - src/lrh/assist/templates/request/work_item_semantic_audit.md
---

# WI-WORK-ITEM-LIFECYCLE-AUDIT-MVP

## Objective

Introduce a lightweight, deterministic work-item lifecycle audit that complements structural validation and supports conservative semantic review of stale or under-evidenced work items.

## Scope

In scope:

- add `lrh work-items audit --format md|json`
- keep audit behavior deterministic and non-mutating
- add validation for structured dependency/reference metadata where deterministically resolvable
- document `organize`, `validate`, and `audit` responsibilities
- add a semantic work-item audit request template
- run the audit on the current proposed bucket and resolve only high-confidence stale work

Out of scope:

- autonomous closure of work items
- LLM-style semantic judgments in validation or audit code
- broad schema redesign
- network-backed issue or project integrations

## Acceptance Criteria

- `lrh work-items audit --format md` emits a human-readable lifecycle report.
- `lrh work-items audit --format json` emits stable schema-versioned JSON.
- `lrh work-items validate` covers deterministic dependency/reference hygiene without claiming implementation completeness.
- Unit tests cover audit formatting, small temp-tree audit behavior, validation reference behavior, and CLI command registration.
- Documentation explains deterministic audit versus semantic review.
- Semantic audit request template asks for conservative, evidence-backed lifecycle recommendations.
- Proposed work items are audited and ambiguous items remain open.

## Expected Evidence

- Code and tests in `src/lrh/work_items/`, `src/lrh/cli/main.py`, and `tests/`.
- Documentation in `project/work_items/README.md` and template README.
- Audit command output from the current repository.
- Standard validation command results.

## Resolution Notes

Implemented in this PR. The proposed bucket audit identified `WI-ASSIST-TEMPLATES-PACKAGING` as a high-confidence stale candidate based on package-owned request templates, package-resource loading, package-data configuration, and tests; that work item was moved to `resolved` with evidence. Other proposed items were left proposed because their lifecycle state requires semantic design review or future implementation evidence.
