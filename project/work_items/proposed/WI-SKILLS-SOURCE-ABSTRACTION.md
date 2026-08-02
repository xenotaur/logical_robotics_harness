---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-SOURCE-ABSTRACTION
title: Add canonical skill source abstraction
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
  - Skill install logic distinguishes canonical source roots from install target roots
  - Package, current-repo, and explicit-path source concepts are represented internally
  - Existing package-source behavior remains covered by regression tests
  - lrh validate reports 0 errors
required_evidence:
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/skills/installer.py
  - tests/skills_installer_test.py
---

# Add canonical skill source abstraction

## Summary

Refactor skill installation so it can enumerate skills from explicit canonical
sources instead of assuming the bundled LRH package tree is the only source.

## Problem / Context

Target-aware installation separates where skills come from from where they are
installed. This work item prepares the installer for package, current-repo, and
explicit-path sources while preserving existing behavior.

## Scope

- Introduce source objects or equivalent internal structure.
- Keep `src/lrh/skills/` authoritative for LRH package skills.
- Add tests for source enumeration and conflict behavior.

## Non-Goals

- Does not add `project/agent_skills.yaml`.
- Does not implement render adapters or ChatGPT export.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
