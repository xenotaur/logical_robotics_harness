---
resolution: completed
blocked_reason: null
blocked: false
id: WI-ASSIST-SOURCETREE-SURVEYOR-MIGRATION
title: Mechanically migrate sourcetree_surveyor into src/lrh/assist/
type: deliverable
status: resolved
priority: medium
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_roadmap:
  - ROADMAP-PHASE-02
depends_on:
  - WI-ASSIST-INSTALLABILITY-HARDENING
blocked_by: []
expected_actions:
  - edit_file
  - add_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - functionality from scripts/aiprog/sourcetree_surveyor.py is migrated into package modules under src/lrh/assist/
  - existing CLI/script behavior remains available through a thin compatibility path
  - migration PR is scoped to relocation and wiring, not feature growth
required_evidence:
  - test_result
  - manual_review
artifacts_expected:
  - code_diff
  - migration_notes
---

## Summary

Mechanical migration is complete: `lrh survey` now delegates to package code in `src/lrh/assist/sourcetree_surveyor.py`, and legacy script-path migration is no longer planned work.
