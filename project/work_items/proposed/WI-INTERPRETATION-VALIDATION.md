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

Verify that LRH not only parses project metadata, but interprets it correctly.

## Goals

- Confirm that focus/work item resolution is semantically correct
- Align implementation with evaluation norms
- Prevent “valid but misunderstood” project state

## Proposed Actions

- Add interpretation-oriented tests
- Validate that active focus, contributors, and work items are resolved correctly
- Add warning/error paths for inconsistent state

## Notes

This work item sits on top of precedence resolution and proves it is useful.
