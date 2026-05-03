---
resolution: null
blocked_reason: null
blocked: false
id: WI-DEV-TOOLCHAIN-RECONCILIATION
title: Reconcile local, CI, and agent validation toolchains
type: operation
status: active
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
  - run_tests
  - run_cli
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - Canonical documentation defines an environment reconciliation workstream.
  - Implementation PR boundaries are explicit and narrowly scoped.
  - Evidence requirements for agent/local/CI mismatch claims are explicit.
required_evidence:
  - manual_review
  - test_result
artifacts_expected:
  - code_diff
  - documentation
  - command_output
---

## Summary

Establish a focused workstream that aligns local development, GitHub Actions,
Codex Cloud, Claude Code, and comparable agent environments on one canonical
validation path and one Black/Ruff expectation set.

## Scope

- Document the reconciliation problem and desired invariant.
- Define version-alignment and canonical-command expectations.
- Define evidence requirements for mismatch claims.
- Establish boundaries for follow-on implementation PRs.

## Non-goals

- No immediate toolchain migration to Docker/devcontainers/uv/Poetry/pip-tools/
  tox/Nox/pre-commit.
- No broad formatting cleanup unrelated to this workstream.
- No manual source rewrapping to fight Black.

## Acceptance Criteria

- The workstream is documented in `project/design/dev_toolchain_reconciliation.md`.
- Follow-on implementation slices are explicit and reviewable.
- Validation and diagnostics evidence expectations are explicit.

## Traceability

- Design: `project/design/dev_toolchain_reconciliation.md`
- Prompt: `PROMPT(AD_HOC:DEV_TOOLCHAIN_RECONCILIATION_DESIGN_ALIGNMENT)[2026-05-03T11:05:00-04:00]`
