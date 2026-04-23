---
resolution: null
blocked_reason: null
blocked: false
id: WI-ASSIST-TEMPLATES-PACKAGING
title: Move assist templates into package-owned runtime location
type: deliverable
status: proposed
priority: high
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_roadmap:
  - ROADMAP-PHASE-02
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
  - request/context templates used at runtime are moved from scripts/aiprog/templates into package-owned paths
  - package-facing docs describe the new canonical template location
  - no runtime behavior depends on repository-root-relative template paths
required_evidence:
  - code_diff
  - test_result
artifacts_expected:
  - code_diff
  - template_tree
---

## Summary

Mechanically relocate assist templates from `scripts/aiprog/templates/` into a package-appropriate location (expected: `src/lrh/assist/templates/`) so installed-package runtime usage is possible.

## Notes

This item is intentionally migration-only. It should not mix in template capability redesign.
