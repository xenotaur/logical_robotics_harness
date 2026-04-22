---
id: WI-ASSIST-SOURCETREE-SURVEYOR-EXPANSION
title: Expand sourcetree_surveyor into Python source-tree audit precursor
type: investigation
status: proposed
priority: medium
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_roadmap:
  - ROADMAP-PHASE-02
depends_on:
  - WI-ASSIST-SOURCETREE-SURVEYOR-MIGRATION
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - proposed expansion scope is documented separately from migration mechanics
  - follow-on enhancements are prioritized for audit use-cases
required_evidence:
  - manual_review
  - evaluation_report
artifacts_expected:
  - design_notes
  - roadmap_update
---

## Summary

Plan and implement capability expansion only after the mechanical migration is complete, to keep changes reviewable and attributable.
