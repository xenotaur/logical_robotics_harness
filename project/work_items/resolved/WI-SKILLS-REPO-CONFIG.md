---
resolution: "Implemented and merged in PR #481 (commit 7271965)"
blocked_reason: null
blocked: false
id: WI-SKILLS-REPO-CONFIG
title: Add project agent skills configuration
type: deliverable
status: resolved
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

## Required Changes

- Define the optional `project/agent_skills.yaml` schema for repository-local
  skill installation configuration, including `schema_version`, configured
  canonical sources, selected targets, install scope, and non-destructive
  install-policy fields.

- Add loader support for `project/agent_skills.yaml` that is optional by
  default: ordinary `lrh skills install` behavior must remain package-source,
  Claude-target compatible when no repo config is present.

- Integrate repo config into skill install planning so configured sources and
  targets can influence the same source/target resolution path used by
  `lrh skills install --source` and `--target`.

- Implement CLI-over-config precedence for install options. Explicit command
  flags must override repo config, and repo config must override conventional
  defaults only where the config explicitly provides a value. Destructive
  overwrite of locally modified skill targets must remain gated by the explicit
  `--force` CLI flag; checked-in repo config must not enable force/overwrite
  behavior on an ordinary `lrh skills install`.

- Address the proposal's YAML parser constraint for list-valued fields: either
  use a real YAML parser for `project/agent_skills.yaml`, or add regression
  coverage proving quoted list-element values are parsed correctly if a simple
  parser is reused.

- Document the schema, precedence order, optional-config behavior, and at least
  one example configuration in repository reference documentation.

- Add focused tests for config loading, absent-config defaults, configured
  source/target influence, CLI-over-config precedence, and quoted list-element
  parsing behavior.

## Non-Goals

- Does not implement target render adapters.
- Does not make config mandatory for ordinary LRH installs.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
