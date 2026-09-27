---
resolution: null
blocked_reason: null
blocked: false
id: WI-LRH-GH-ERROR-CLASSIFICATION
title: Distinguish LRH GitHub wrapper failure classes
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-LRH-GITHUB-EXECUTION-RESILIENCE
related_design: []
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - add_live_network_unit_tests
acceptance:
  - An invalid subprocess working directory is reported as an invalid project root, not `gh CLI not found`.
  - A missing `gh` executable is reported distinctly from an invalid working directory.
  - A nonzero `gh` exit preserves a sanitized, actionable stderr category such as DNS, authentication, or API failure.
  - Malformed JSON remains distinguishable from process-launch and GitHub command failures.
  - Unit tests cover each classification with mocked subprocess behavior and no network dependency.
  - "`lrh validate` and canonical test/lint/format checks pass."
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/integrations/github/gh_client.py
  - src/lrh/prompt_workflow_slug.py
  - tests/integrations_tests/github_integration_test.py
---

# Distinguish LRH GitHub wrapper failure classes

## Summary

LRH currently catches every `FileNotFoundError` from `subprocess.run` and
reports `gh CLI not found`. Python raises the same exception when the requested
subprocess `cwd` does not exist, so a caller using the wrong relative
`--project-root` receives a misleading executable diagnostic.

## Problem / Context

The wrapper launches `gh` with a caller-supplied `cwd` and maps all
`FileNotFoundError` cases to one message. The prompt workflow then adds the
generic `gh pr list failed` context. This obscures the distinction between a
local project-root mistake, a missing binary, and a genuine network/API error.

### Duplication search

- In-repo: Related implementation exists in
  `src/lrh/integrations/github/gh_client.py`; no separate error taxonomy exists.
- Sibling repos: None identified.
- External libraries: None required; standard-library subprocess behavior is
  sufficient.
- Recommendation: Extend the existing wrapper and tests.

### Demand search

- Work items: No matching proposed item found.
- Proposals: No matching proposal found.
- Backlog: No separate matching entry; this item complements the Codex network
  guidance demand.
- Recommendation: Proceed.

## Scope

- Validate or classify the requested working directory before launching `gh`.
- Preserve the current nonzero-exit and JSON validation behavior while giving
  failures distinct, actionable categories.
- Add hermetic unittest coverage for launch, cwd, command, and output failures.

## Required Changes

1. Update `src/lrh/integrations/github/gh_client.py` to distinguish invalid
   `cwd` from missing executable and nonzero `gh` exit.
2. Update `src/lrh/prompt_workflow_slug.py` only as needed to preserve the
   useful operation context without erasing the inner category.
3. Add tests to `tests/integrations_tests/github_integration_test.py` for each
   failure class.
4. Run the canonical formatter, linter, tests, and validator.

## Non-Goals

- Do not change GitHub authentication behavior.
- Do not add retries or hide network failures.
- Do not add live GitHub calls to the unit suite.
- Do not change idempotence semantics or make remote checks silently optional.

## Acceptance Criteria

- The wrong relative project root produces an actionable project-root error.
- Missing `gh`, DNS/API failure, and malformed JSON produce distinct errors.
- Existing successful GitHub wrapper behavior remains unchanged.
- All new tests use `unittest.TestCase` and mocked/in-process boundaries.
- `scripts/version tools`, `scripts/format --check --diff`, `scripts/lint`,
  `scripts/test`, `lrh validate`, and `git diff --check` pass.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `git diff --check`

## Risk Notes

- Error-message changes may affect callers or tests; preserve the outer
  operation context and update only the classification contract.
- Do not infer credential failure from DNS or process-launch errors.
