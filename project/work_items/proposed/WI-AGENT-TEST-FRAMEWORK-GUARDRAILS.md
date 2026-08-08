---
id: WI-AGENT-TEST-FRAMEWORK-GUARDRAILS
title: Enforce unittest and canonical scripts via AGENTS.md and Ruff banned-api
type: operation
status: proposed
blocked: false
blocked_reason: null
resolution: null
related_workstreams: []
depends_on: []
blocked_by: []
artifacts_expected:
  - AGENTS.md
  - pyproject.toml
  - .claude/skills/lrh-implement/references/canonical-validation.md
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - AGENTS.md includes explicit Testing and Validation Mandate section requiring standard library unittest and canonical script wrappers.
  - pyproject.toml configures Ruff flake8-tidy-imports (banned-api) for pytest with message citing STYLE.md Rule 5.
  - .claude/skills/lrh-implement/references/canonical-validation.md is updated to reference unittest.TestCase requirement.
  - lrh validate reports 0 errors.
---

# WI-AGENT-TEST-FRAMEWORK-GUARDRAILS: Enforce unittest and canonical scripts via AGENTS.md and Ruff banned-api

## Summary

Establish a two-layer closed-loop guidance system ("coming and going") to enforce standard library `unittest` usage and canonical script wrappers (`scripts/test`, `scripts/lint`, `scripts/format`) across all AI agents and human contributors. Upfront prompt directives are placed in `AGENTS.md`, and mechanical lint enforcement is configured in `pyproject.toml` via Ruff's `banned-api` rule citing `STYLE.md Rule 5`.

## Problem / Context

Previous agent sessions wrote tests using `import pytest`, pytest fixtures (`tmp_path`), and standalone `def test_*` functions. Because `pytest` was installed in local virtualenvs, `pytest tests/` passed locally, but `python -m unittest discover` (which `scripts/test` and CI run) silently ignored un-classed test functions or failed on missing `pytest` dependencies in CI environments.

### Prior Art Check
- Duplication search: No existing `banned-api` configuration in `pyproject.toml` or `scripts/lint`. Related design doc: `project/design/dev_toolchain_reconciliation.md`.
- Demand search: No open work items in `project/work_items/proposed/`.

## Scope

### Included
- Update `AGENTS.md` with explicit Testing and Validation Mandate section.
- Update `pyproject.toml` to select `TID` in Ruff and add `banned-api` configuration for `pytest` pointing to `STYLE.md Rule 5`.
- Update `.claude/skills/lrh-implement/references/canonical-validation.md` to reference `unittest.TestCase` requirements.

### Excluded
- Re-architecting existing test files or changing test runners.

## Required Changes

### `AGENTS.md`
- Add `## Testing and Validation Mandate` section under `## Environment setup before validation`.

### `pyproject.toml`
- Add `"TID"` to `[tool.ruff.lint] select`.
- Add `[tool.ruff.lint.flake8-tidy-imports.banned-api]` section with `"pytest".msg` citing `STYLE.md Rule 5`.

### `.claude/skills/lrh-implement/references/canonical-validation.md`
- Clarify test discovery rules and `unittest.TestCase` requirements under `scripts/test`.

## Non-Goals
- Adding third-party testing dependencies.

## Acceptance Criteria

- `AGENTS.md` includes explicit Testing and Validation Mandate section requiring standard library `unittest` and canonical script wrappers.
- `pyproject.toml` configures Ruff `flake8-tidy-imports` (`banned-api`) for `pytest` with message citing `STYLE.md Rule 5`.
- `.claude/skills/lrh-implement/references/canonical-validation.md` is updated to reference `unittest.TestCase` requirement.
- `lrh validate` reports 0 errors.

## Validation

- `lrh validate`
- `scripts/lint`
- `scripts/test`

## Risk Notes

- Low risk: Only affects linting rules for forbidden `pytest` imports and documentation guardrails.
