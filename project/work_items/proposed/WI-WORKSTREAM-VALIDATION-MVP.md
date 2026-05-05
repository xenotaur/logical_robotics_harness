---
resolution: null
blocked_reason: null
blocked: false
id: WI-WORKSTREAM-VALIDATION-MVP
title: Validate workstream metadata, IDs, and bucket/status consistency
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-WORKSTREAM-CONTROL-PLANE-MVP
related_roadmap:
  - ROADMAP-PHASE-01
depends_on:
  - WI-WORKSTREAM-LOADER-MODEL-MVP
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - required metadata and valid status/stage are validated
  - unique IDs and bucket/status drift are validated
required_evidence:
  - test_result
artifacts_expected:
  - code_diff
  - test_module
---

## Summary

Add control-plane validation for workstream metadata authority, valid lifecycle values,
unique identity, and directory projection consistency.
