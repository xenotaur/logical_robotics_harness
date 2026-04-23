---
resolution: null
blocked_reason: null
blocked: false
id: WI-ASSIST-INSTALLABILITY-HARDENING
title: Harden installed-package template loading and packaging smoke checks
type: operation
status: proposed
priority: high
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_roadmap:
  - ROADMAP-PHASE-02
depends_on:
  - WI-ASSIST-TEMPLATES-PACKAGING
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - template loading uses package resources rather than source-tree-relative paths
  - install/build flow includes smoke checks for `lrh request` and `lrh snapshot` behavior from an installed package context
  - documentation records installed-package expectations
required_evidence:
  - test_result
  - manual_review
artifacts_expected:
  - code_diff
  - smoke_test_output
---

## Summary

Treat package-data correctness and installed-package behavior as first-class requirements before broader collaborator-facing publication.
