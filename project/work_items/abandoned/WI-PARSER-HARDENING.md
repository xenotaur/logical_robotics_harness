---
resolution: "Superseded by PROP-LRH-FRONTMATTER-PARSER (WS-LRH-FRONTMATTER-PARSER), the same proposal that superseded the more specific WI-VALIDATOR-YAML-PARSER. This WI's broader ask (harden or replace the bootstrap frontmatter parser) is fully covered by that proposal's parser consolidation, content-safety migration, and lint-guard design. Missed during the proposal's original prior-art search (its search terms didn't match this WI's older vocabulary); found and closed as a follow-up."
blocked_reason: null
blocked: false
id: WI-PARSER-HARDENING
title: Replace or harden bootstrap frontmatter parsing
type: investigation
status: abandoned
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

## Superseded

Superseded by [`PROP-LRH-FRONTMATTER-PARSER`](../../design/proposals/proposed/lrh-frontmatter-parser/00_proposal.md)
and its governing workstream [`WS-LRH-FRONTMATTER-PARSER`](../../workstreams/proposed/WS-LRH-FRONTMATTER-PARSER.md) —
the same proposal that already superseded the more specific
[`WI-VALIDATOR-YAML-PARSER`](WI-VALIDATOR-YAML-PARSER.md). This WI predates
that proposal (2026-04-14) and was missed by its original prior-art search
because this file never uses the later vocabulary ("hand-rolled",
"`_parse_frontmatter_mapping`") the search grepped for; it was found only
once landing that proposal's implementation work items surfaced it.

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
