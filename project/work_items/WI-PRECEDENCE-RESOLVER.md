---
id: WI-PRECEDENCE-RESOLVER
title: Implement control-plane precedence resolver
type: deliverable
status: proposed
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

Implement the first precedence resolver for LRH’s control plane.

## Goals

- Make precedence operational rather than purely documented
- Resolve active focus and in-scope work from project artifacts
- Support future snapshot/status interpretation

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

## Notes

This is the central remaining gap in Phase 1.
