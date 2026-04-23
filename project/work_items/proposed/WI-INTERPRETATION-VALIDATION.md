---
resolution: null
blocked_reason: null
blocked: false
id: WI-INTERPRETATION-VALIDATION
title: Validate semantic interpretation of focus and work items
type: evaluation
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-CONTROL-PLANE-SEMANTICS
related_roadmap:
  - ROADMAP-PHASE-01
depends_on:
  - WI-PRECEDENCE-RESOLVER
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - LRH can identify current focus correctly
  - LRH can identify active contributors correctly
  - LRH can identify relevant work items correctly
  - interpretation failures produce clear warnings or errors
required_evidence:
  - test_result
  - manual_review
artifacts_expected:
  - code_diff
  - test_module
  - interpretation_notes
---

## Summary

Validate that LRH interprets precedence-resolved control-plane state correctly for focus,
contributors, and relevant work items.

## Problem

Precedence resolution is implemented, but interpretation behavior still needs explicit validation.
Without focused interpretation checks, LRH can appear valid while resolving ambiguous or
inconsistent project state incorrectly.

## Scope

In scope:

- Add focused tests that verify resolved interpretation behavior for:
  - current focus
  - active contributors
  - relevant work items
- Validate that inconsistent or ambiguous resolved state is surfaced through clear
  warnings/findings/errors, as appropriate to current validator behavior.
- Make only minimal supporting code changes required to enable or expose these checks.

## Out of Scope

- Redesigning precedence semantics or changing precedence ordering
- Broad refactors of loaders, CLI, or control-plane architecture
- Snapshot output redesign
- New planning schema or work-item model changes
- Follow-on hardening outside focused interpretation validation

## Likely Files

- `tests/control_plane/test_precedence.py` (extend with interpretation-focused cases)
- `tests/control_plane/` additional focused interpretation test module (if clearer than
  extending existing tests)
- `src/lrh/control_plane/precedence.py` (only if minimal supporting changes are required)
- `src/lrh/control/validator.py` (only if needed to surface interpretation findings used by `lrh validate`)

## Required Changes

- Add focused interpretation tests that exercise precedence-resolved project state.
- Assert correct resolution for:
  - current focus
  - active contributors
  - relevant work items
- Add expectations for inconsistent/ambiguous state handling, including warning or error
  surfaces in the active `lrh validate` flow where currently supported.
- Keep changes conservative and limited to interpretation validation behavior.

## Validation

- Run `scripts/test`
- Run `scripts/validate`
- Confirm new interpretation tests pass and no unrelated regressions are introduced.
- Manually review representative resolved outputs/findings to confirm they match expected
  interpretation.

## Acceptance Criteria

- Focused tests exist for interpretation of focus, contributors, and relevant work items.
- Tests demonstrate correct behavior on valid resolved state.
- Tests demonstrate clear surfaced findings for inconsistent/ambiguous resolved state.
- Any supporting code changes are minimal and scoped to interpretation validation.
- No unrelated modules or work items are modified.

## Notes

This work item follows `WI-PRECEDENCE-RESOLVER` and stays within Phase 1 control-plane
semantics. The goal is confidence in interpretation behavior, not broad redesign.
