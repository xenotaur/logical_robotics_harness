---
id: WI-PRECEDENCE-RESOLVER
title: Implement control-plane precedence resolver
type: deliverable
status: done
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-CONTROL-PLANE-SEMANTICS
related_roadmap:
  - ROADMAP-PHASE-01
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
  - LRH implements a precedence model consistent with the design document
  - precedence resolution can identify the active focus and in-scope work items
  - precedence behavior is deterministic
  - precedence logic is covered by focused tests
required_evidence:
  - test_result
  - manual_review
artifacts_expected:
  - code_diff
  - resolver_module
  - test_module
---

## Summary

Implement a deterministic precedence resolver for LRH’s control plane, enabling the system to
interpret the effective project state (focus, active work items, contributors) from project/
artifacts.

## Goals

- Make precedence operational rather than purely documented
- Resolve active focus and in-scope work from project artifacts
- Support future snapshot/status interpretation

## Problem

LRH currently parses project metadata but does not interpret it using a defined precedence model.
As a result, the system cannot reliably determine:

- the active focus
- the set of in-scope work items
- the effective contributors

This limits LRH to validation rather than control-plane reasoning.

## Proposed Actions

- Implement precedence resolution in code
- Use the design-defined ordering of:
  - principles
  - goal
  - roadmap
  - focus
  - work items
  - guardrails
  - runtime invocation
- Add focused tests for correct precedence behavior

## Scope

In scope:

- Implement a precedence resolver consistent with the design.md precedence model
- Resolve:
  - current focus
  - active contributors
  - in-scope work items
- Ensure deterministic behavior (same inputs → same outputs)
- Expose resolution through a callable module or function
- Add focused unit tests for precedence behavior

---

## Out of Scope

- Snapshot output changes (handled by separate work item)
- CLI interface redesign
- Schema changes to project/ files
- Broad refactors of loaders or validators
- Performance optimization beyond basic correctness
- Any redesign of precedence rules beyond what is already in design.md

---

## Likely Files

- lrh/control_plane/precedence.py (new)
- lrh/control_plane/__init__.py (if needed)
- lrh/loaders/* (read-only usage only, no refactor unless strictly required)
- tests/control_plane/test_precedence.py (new)

---

## Required Changes

- Create a precedence resolver module
- Implement precedence ordering as defined in design.md:
  - principles
  - goal
  - roadmap
  - focus
  - work items
  - guardrails
  - runtime invocation
- Implement functions to:
  - determine active focus
  - determine active contributors
  - determine relevant work items
- Ensure resolver is pure and deterministic (no hidden state)
- Add unit tests covering:
  - simple valid project state
  - conflicting signals (if representable)
  - missing optional components

---

## Acceptance Criteria

- Resolver produces consistent outputs for the same project state
- Resolver correctly identifies:
  - current focus
  - active contributors
  - relevant work items
- Behavior matches precedence model described in design.md
- Unit tests exist and pass
- No unrelated files are modified

---

## Validation

- Run:
  - `scripts/test`
  - `scripts/validate`
- Confirm:
  - no regression in existing validation behavior
  - new tests pass
- Manual sanity check:
  - resolver output matches expected interpretation of project/

---

## Required Evidence

- test_result
- manual_review

---

## Artifacts Expected

- code_diff
- precedence_module
- test_module

---

## Notes

This is the central remaining gap in Phase 1.
This is the core semantic step of Phase 1: moving from parsing → interpretation.
Keep implementation minimal and conservative. If any ambiguity in precedence rules is encountered, do not guess—surface it clearly.

## Completion Notes

- Completed: deterministic precedence resolution is implemented in `src/lrh/control_plane/precedence.py`.
- Completed: precedence behavior is covered by `tests/control_plane/test_precedence.py`.
- 2026-04-22 closure validation: canonical precedence source is `project/memory/decisions/precedence_semantics.md`; docs, implementation, and tests are aligned with narrowing-only semantics.
- 2026-04-22 closure validation: no unresolved correctness follow-up items were identified for precedence canonicalization.
