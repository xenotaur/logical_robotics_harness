---
resolution: null
blocked_reason: null
blocked: false
id: WI-ASSIST-TEMPLATES-PACKAGING
title: Move assist templates into package-owned runtime location
type: deliverable
status: proposed
priority: high
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_roadmap:
  - ROADMAP-PHASE-02
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - add_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - request/context templates used at runtime are moved from scripts/aiprog/templates into package-owned paths
  - package-facing docs describe the new canonical template location
  - no runtime behavior depends on repository-root-relative template paths
required_evidence:
  - code_diff
  - test_result
artifacts_expected:
  - code_diff
  - template_tree
---

## Summary

Mechanically relocate assist runtime templates from `scripts/aiprog/templates/` into a package-owned location (expected: `src/lrh/assist/templates/`) so installed-package usage does not depend on repository-root-relative paths.

## Objective

Make assist runtime template loading install-safe by using package-owned template files and package-resource loading semantics, while preserving existing template behavior and CLI-visible behavior.

## Scope

In scope:

- move runtime request/context templates into `src/lrh/assist/templates/` (or equivalent package-owned path)
- update runtime template loading to use package-resource semantics suitable for installed distributions
- preserve existing template content and behavior (migration-only)
- add or update focused tests/smoke checks covering installed-package template loading behavior
- update package-facing docs only where needed to describe canonical runtime template location

## Out of Scope

- redesigning prompt templates or changing template capabilities
- expanding assist feature surface
- unrelated refactors in `src/lrh/assist/` or elsewhere
- broad documentation cleanup beyond migration-specific updates
- roadmap/focus restructuring

## Likely Files

Work-item refinement (this PR):

- `project/work_items/proposed/WI-ASSIST-TEMPLATES-PACKAGING.md`

Likely implementation targets (future PR):

- `src/lrh/assist/templates/`
- `src/lrh/assist/request_templates.py`
- `pyproject.toml`
- assist template-loading tests and/or installed-behavior smoke coverage
- `src/lrh/assist/README.md` (only if template location docs need update)
- `scripts/README.md` (only if script usage docs need update)

## Required Changes

For the future implementation PR, expected change shape is:

1. mechanical template move from `scripts/aiprog/templates/` to package-owned runtime location
2. template loader update to package-resource access pattern
3. behavior-preserving migration (no template capability redesign)
4. focused tests/smoke checks for installed-package template loading
5. minimal documentation updates tied directly to canonical template location and runtime loading

## Validation

For the future implementation PR, validate with existing repository commands:

- `scripts/validate`
- `scripts/test`
- `scripts/smoke_assist_install`

## Acceptance Criteria

- assist runtime templates are package-owned and no longer loaded via repository-root-relative paths
- assist runtime loading uses package-resource semantics compatible with installed usage
- existing assist template behavior remains unchanged (migration-only)
- focused automated coverage verifies installed-package template loading path
- docs mention canonical package-owned runtime template location where applicable
- sequencing intent is preserved: this migration lands before installability hardening and `sourcetree_surveyor` migration work items

## Notes

This item is intentionally migration-only and sequencing-sensitive. It should remain a mechanical packaging/runtime-location change, not a template redesign.
