---
id: WI-VALIDATOR-PROJECT-CLEANUP
title: Fix project metadata to pass validator
type: operation
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-1
depends_on: []
blocked_by: []
---

## Summary

The current `project/` directory does not pass validation (reported errors and warnings from `lrh validate`).

This work item brings all project metadata into compliance with the validator.

## Goals

- Achieve zero validation errors
- Minimize warnings where appropriate
- Ensure consistency with contributor and ownership semantics

## Proposed Actions

- Run `lrh validate`
- Fix:
  - missing required fields
  - invalid enums
  - unknown references
  - owner / contributor inconsistencies
- Review warnings and resolve where appropriate

## Acceptance Criteria

- `lrh validate` reports:
  - 0 errors
  - acceptable or documented warnings
- All contributor references resolve
- All ownership semantics align with design

## Notes

This is required before enabling validator enforcement in CI.
