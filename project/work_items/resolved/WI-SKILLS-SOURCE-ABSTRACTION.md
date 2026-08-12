---
resolution: "Implemented canonical skill source abstraction and merged in PR #477 (commit d05b9ccc2593ac29ced343d559b25a2be2f21436)."
blocked_reason: null
blocked: false
id: WI-SKILLS-SOURCE-ABSTRACTION
title: Add canonical skill source abstraction
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
  - project/design/proposals/adopted/lrh-skills-target-aware-install/00_proposal.md
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

## Required Changes

- Add an internal canonical skill source abstraction that can represent the
  bundled LRH package source, the current repository's canonical skill source,
  and an explicit filesystem path source.

- Refactor skill enumeration so install planning reads from a selected source
  abstraction instead of assuming the bundled `src/lrh/skills/` package tree is
  the only possible source.

- Add a `--source` CLI selection surface for `lrh skills install` that exposes
  the bundled LRH package source, the current repository source, and an explicit
  filesystem path source.

- Preserve existing package-source behavior as the default path used by current
  `lrh skills install` commands.

- Keep install target directories (`.claude/skills/`, `.agents/skills/`, and
  user-scope equivalents) as generated destinations rather than authoritative
  canonical sources.

- Add focused regression tests for package-source enumeration and for at least
  one non-package source path, including conflict or destination behavior that
  proves source selection does not bypass existing install safety checks.

- Add CLI tests showing that `--source` selects each supported source form and
  that the default command path remains package-source compatible.

## Non-Goals

- Does not add `project/agent_skills.yaml`.
- Does not implement render adapters or ChatGPT export.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
