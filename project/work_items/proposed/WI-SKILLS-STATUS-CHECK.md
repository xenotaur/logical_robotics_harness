---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-STATUS-CHECK
title: Add skill install status and check commands
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-SKILLS-TARGET-AWARE-INSTALL
related_design:
  - project/design/proposals/proposed/lrh-skills-target-aware-install/00_proposal.md
depends_on:
  - WI-SKILLS-TARGET-AWARE-INSTALL
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - `lrh skills status` reports installed, missing, modified, and target-specific skill states
  - `lrh skills check` reports unsupported metadata and target drift without writing files
  - Commands support Claude and Codex targets
  - Human-readable output is covered by focused tests
  - lrh validate reports 0 errors
required_evidence:
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/cli/main.py
  - src/lrh/skills/installer.py
  - tests/cli_tests/skills_test.py
  - tests/skills_installer_test.py
---

# Add skill install status and check commands

## Summary

Add read-only commands for inspecting skill install state, target drift, and
compatibility issues before writing any target files.

## Problem / Context

Target-aware installs make it more important to see what would change across
Claude and Codex directories. Status and check commands give maintainers a
safe, reviewable way to inspect drift and unsupported metadata.

## Scope

- Add `lrh skills status`.
- Add `lrh skills check`.
- Report installed/missing/modified states per target.
- Report unsupported or untranslated metadata.

## Non-Goals

- Does not write skill files.
- Does not implement ChatGPT export.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
