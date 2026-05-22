---
resolution: null
blocked_reason: null
blocked: false
id: WI-DOCS-SCHEMA-REFERENCE-SEED
title: Seed schema reference pages for implemented control-plane contracts
type: deliverable
status: proposed
priority: medium
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams: []
related_design: []
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - docs/reference/schemas includes at least one concrete implemented schema page
  - schema docs clearly distinguish authoritative contracts from design-stage proposals
  - schema docs link to relevant validator behavior and project-control source examples
required_evidence:
  - manual_review
artifacts_expected:
  - documentation
---

## Summary

Populate `docs/reference/schemas/` with initial pages for already-implemented LRH control-plane contracts so the section is no longer empty placeholder navigation.

## Scope

- Start with one or two high-value implemented contracts.
- Cross-link validator/reference behavior and source artifact examples.
- Keep each page contract-focused rather than procedural.

## Non-Goals

- Do not document speculative or not-yet-implemented schema fields as current behavior.
- Do not rewrite all project-control documentation in one pass.
