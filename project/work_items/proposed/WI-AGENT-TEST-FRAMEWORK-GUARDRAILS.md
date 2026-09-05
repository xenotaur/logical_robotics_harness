---
id: WI-AGENT-TEST-FRAMEWORK-GUARDRAILS
title: Enforce unittest and canonical scripts via AGENTS.md and Ruff banned-api
type: operation
status: proposed
owner: null
contributors: []
assigned_agents: []
related_focus: []
related_roadmap: []
related_design: []
related_workstreams: []
depends_on: []
blocked_by: []
blocked: false
blocked_reason: null
resolution: null
expected_actions: []
required_evidence: []
artifacts_expected:
  - AGENTS.md
  - pyproject.toml
  - src/lrh/skills/lrh-implement/references/canonical-validation.md
  - .claude/skills/lrh-implement/references/canonical-validation.md
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - AGENTS.md includes explicit Testing and Validation Mandate section requiring standard library unittest and canonical script wrappers.
  - pyproject.toml configures Ruff flake8-tidy-imports (banned-api) for pytest with message citing STYLE.md Rule 5.
  - Both src/lrh/skills/ and .claude/skills/ copies of canonical-validation.md reference unittest.TestCase requirement and pass diff -r sync check.
  - lrh validate reports 0 errors.
---

# WI-AGENT-TEST-FRAMEWORK-GUARDRAILS: Enforce unittest and canonical scripts via AGENTS.md and Ruff banned-api

## Summary

Establish a two-layer closed-loop guidance system ("coming and going") to enforce standard library `unittest` usage and canonical script wrappers (`scripts/test`, `scripts/lint`, `scripts/format`) across all AI agents and human contributors. Upfront prompt directives are placed in `AGENTS.md`, and mechanical lint enforcement is configured in `pyproject.toml` via Ruff's `banned-api` rule citing `STYLE.md Rule 5`.

## Problem / Context

Previous agent sessions wrote tests using `import pytest`, pytest fixtures (`tmp_path`), and standalone `def test_*` functions (such as in PR #526). Because `pytest` was installed in local virtualenvs, `pytest tests/` passed locally, but `python -m unittest discover` (which `scripts/test` and CI run) silently ignored un-classed test functions or failed on missing `pytest` dependencies in CI environments. While PR #528 resolved the immediate test breakage on `main` by converting `tests/conversations_tests/antigravity_export_test.py` to `unittest.TestCase`, systemic guardrails are required to prevent recurrence across future sessions.

### Duplication search
- In-repo: PR #528 fixed the specific broken test on `main`. No existing `banned-api` configuration in `pyproject.toml` or `scripts/lint`. Related design doc: `project/design/dev_toolchain_reconciliation.md`.
- Sibling repos: None identified.
- External libraries: Ruff native `flake8-tidy-imports` (`TID253`) provides `banned-api` configuration in `pyproject.toml`.
- Recommendation: Proceed with work item creation.

### Demand search
- Work items: None found in `project/work_items/proposed/`.
- Proposals: None found in `project/design/proposals/`.
- Backlog: No matching entries in `project/design/backlog.md`.
- Recommendation: No existing work item to close or link.

## Scope

### Included
- Update `AGENTS.md` with explicit Testing and Validation Mandate section.
- Update `pyproject.toml` to select `TID` in Ruff and add `banned-api` configuration for `pytest` pointing to `STYLE.md Rule 5`.
- Update both `src/lrh/skills/lrh-implement/references/canonical-validation.md` and `.claude/skills/lrh-implement/references/canonical-validation.md` to reference `unittest.TestCase` requirements and maintain byte-for-byte synchronization.

### Excluded
- Re-architecting unrelated test files or adding external test dependencies.

## Required Changes

### `AGENTS.md`
- Add `## Testing and Validation Mandate` section under `## Environment setup before validation`.

### `pyproject.toml`
- Add `"TID"` to `[tool.ruff.lint] select`.
- Add `[tool.ruff.lint.flake8-tidy-imports.banned-api]` section with `"pytest".msg` citing `STYLE.md Rule 5`.

### Skill Reference Docs
- Update `src/lrh/skills/lrh-implement/references/canonical-validation.md` and `.claude/skills/lrh-implement/references/canonical-validation.md` to clarify test discovery rules and `unittest.TestCase` requirements under `scripts/test`.

## Non-Goals
- Adding third-party testing dependencies.

## Acceptance Criteria

- `AGENTS.md` includes explicit Testing and Validation Mandate section requiring standard library `unittest` and canonical script wrappers.
- `pyproject.toml` configures Ruff `flake8-tidy-imports` (`banned-api`) for `pytest` with message citing `STYLE.md Rule 5`.
- Both `src/lrh/skills/` and `.claude/skills/` copies of `canonical-validation.md` reference `unittest.TestCase` requirement and pass `diff -r` sync check.
- `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `diff -r src/lrh/skills/lrh-implement/ .claude/skills/lrh-implement/`

## Risk Notes

- Low risk: Ensures immediate compatibility between Ruff linter rules, test suite discovery, and agent prompt guidance.
