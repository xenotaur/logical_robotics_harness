---
resolution: null
blocked_reason: null
blocked: false
id: WI-DOCS-CLI-OPTION-TABLES
title: Add maintainable CLI option tables for high-traffic commands
type: deliverable
status: proposed
priority: low
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
  - reference CLI docs include concise option tables for validate, snapshot, survey, request, meta, and serve
  - tables reflect current --help output and do not include planned flags
  - documentation update remains maintainable and avoids duplicating full help text
required_evidence:
  - manual_review
artifacts_expected:
  - documentation
---

## Summary

Add concise, maintainable option tables for high-traffic CLI commands so users can quickly scan flags without reading full prose or terminal help output.

## Scope

- Add option tables to the most-used command reference pages.
- Keep table rows aligned with current `lrh ... --help` output only.
- Preserve concise command-purpose and behavior-limit sections.

## Non-Goals

- Do not generate a docs site or autogeneration pipeline in this item.
- Do not change CLI behavior.
