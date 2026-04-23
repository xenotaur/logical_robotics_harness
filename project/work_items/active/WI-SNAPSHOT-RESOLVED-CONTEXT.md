---
id: WI-SNAPSHOT-RESOLVED-CONTEXT
title: Make snapshot output reflect resolved control-plane context
type: deliverable
status: active
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
depends_on:
  - WI-PRECEDENCE-RESOLVER
  - WI-INTERPRETATION-VALIDATION
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - snapshot output reflects resolved current focus
  - snapshot output reflects active contributors and relevant work items
  - snapshot output surfaces precedence or interpretation findings where appropriate
required_evidence:
  - manual_review
  - test_result
artifacts_expected:
  - code_diff
  - snapshot_output
  - test_module
---
## Summary

Update snapshot tooling so it reports resolved project state rather than only file summaries.

## Goals

- Prove that precedence and interpretation are operational
- Improve control-plane observability
- Provide a useful human-readable project state packet

## Proposed Actions

- Make snapshot consume resolved control-plane context
- Include current focus, active contributors, and relevant work items
- Include warnings or notes for inconsistency when useful

## Notes

This is the clearest user-facing proof that Phase 1 semantics are working.

## Progress Notes

- 2026-04-22: `lrh snapshot` is now a package CLI entrypoint (`lrh snapshot ...`) with dedicated assist module code.
- 2026-04-22: Snapshot packets include structured summaries and focus-related work item filtering, but do not yet consume full precedence-resolved contributor/context outputs.
