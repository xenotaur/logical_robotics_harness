---
id: WI-PARSER-HARDENING
title: Replace or harden bootstrap frontmatter parsing
type: investigation
status: proposed
blocked: false
blocked_reason: null
resolution: null
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
  - parser limitations are documented or removed
  - realistic frontmatter inputs are handled reliably
  - parsing behavior is covered by focused tests
required_evidence:
  - test_result
  - manual_review
artifacts_expected:
  - code_diff
  - parser_notes
  - test_module
---
## Summary

Strengthen or replace the bootstrap frontmatter parser used by LRH.

## Goals

- Reduce risk of silent metadata misinterpretation
- Improve parsing reliability for realistic Markdown/YAML inputs
- Support the control plane as stable infrastructure

## Proposed Actions

- Evaluate whether to keep, harden, or replace the current parser
- Add realistic parsing tests
- Implement the minimal robust solution

## Notes

This remains one of the largest technical risks in Phase 1.
