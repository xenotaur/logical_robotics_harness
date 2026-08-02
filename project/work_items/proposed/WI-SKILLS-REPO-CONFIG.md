---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-REPO-CONFIG
title: Add project agent skills configuration
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
  - WI-SKILLS-SOURCE-ABSTRACTION
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - `project/agent_skills.yaml` schema and precedence are documented
  - Configured sources and targets influence install planning
  - CLI flags override repo config where specified
  - Quoted list-element values are parsed correctly or covered by regression tests if a simple parser is reused
  - lrh validate reports 0 errors
required_evidence:
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/skills/installer.py
  - docs/reference
  - tests/skills_installer_test.py
---

# Add project agent skills configuration

## Summary

Add repository-local skill install configuration through
`project/agent_skills.yaml`, including source, target, scope, and install-policy
settings.

## Problem / Context

The proposal adopts repo-local configuration so LRH-managed projects can define
their own canonical skill sources and preferred install targets. The parser
choice matters because list-valued YAML has previously been a fragile shape in
the control-plane parser.

## Scope

- Define and document the configuration schema.
- Load config during install planning.
- Apply CLI-over-config precedence.
- Add parser regression coverage for list-valued config.

## Non-Goals

- Does not implement target render adapters.
- Does not make config mandatory for ordinary LRH installs.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
