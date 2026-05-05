---
resolution: null
blocked_reason: null
blocked: false
id: WI-WORKSTREAM-SCHEMA-MVP
title: Define minimal workstream frontmatter and status/stage semantics
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
  - WI-WORKSTREAM-DIRECTORY-README-MVP
blocked_by: []
expected_actions:
  - edit_file
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - minimal workstream metadata schema is documented
  - status/stage semantics are explicit and reviewable
required_evidence:
  - manual_review
artifacts_expected:
  - code_diff
  - documentation
---

## Summary

Define documentation-level minimal schema for workstreams, including required IDs,
status buckets, stage semantics, and parent/child reference fields.
