# Dev Toolchain Reconciliation: Local, CI, and Agent Environments

## Purpose

Define a focused LRH workstream that reconciles local development, GitHub Actions,
Codex Cloud, Claude Code, and comparable agent environments so they run the same
canonical validation path with the same Black/Ruff expectations.

This document is design alignment only. It does not implement toolchain changes.

## Problem Statement

LRH has recurring noisy failures where one environment reports Black/Ruff or
validation drift that another environment cannot reproduce for the same branch.

Observed failure patterns include:

- `scripts/lint` reporting Ruff success but Black-related check failures in CI or
  agent environments.
- local runs at branch head passing `scripts/format`, `scripts/lint`, and
  `scripts/test`, while Codex Cloud or CI report pre-existing formatting drift.
- agent reports claiming pass/fail outcomes without enough evidence for
  maintainers to reproduce quickly.

These mismatches slow reviews and create avoidable prompt/PR churn.

## Desired Invariant

For the same commit SHA, with the same documented setup path and canonical
commands, LRH should produce the same validation result in local, CI, Codex
Cloud, Claude Code, and similar agent environments.

Canonical commands:

- `scripts/format`
- `scripts/lint`
- `scripts/test`

## Technical Direction

### 1) Constrain the formatter/linter toolchain

- Define constrained or pinned Black/Ruff versions in one canonical location.
- Avoid implicit tool upgrades in one environment but not others.

### 2) Enforce runtime version compatibility where supported

- Add Black and Ruff runtime version checks (or equivalent guardrails) in
  canonical scripts and/or CI bootstrap.
- Fail fast when tool versions are outside supported bounds.

### 3) Keep CI on the same path as local and agent runs

- CI should call the same canonical scripts used by local contributors and
  agents rather than hand-rolled direct tool invocations.
- Setup instructions should describe one path that all environments follow.

### 4) Require agents to use canonical scripts

- Agent workflows should run `scripts/format`, `scripts/lint`, and `scripts/test`
  rather than substituting direct `black`, `ruff`, or `pytest` commands unless
  explicitly required for targeted debugging.

### 5) Standardize diagnostics and evidence

Validation reports should include enough reproducibility context to evaluate
cross-environment drift quickly:

- commit SHA
- clean/dirty working tree status
- Python version
- Black/Ruff versions
- canonical command outputs
- relevant formatting or lint diffs when failures occur

## Non-goals

This workstream explicitly does **not** include, in its initial slice:

- introducing Docker, dev containers, uv, Poetry, pip-tools, tox, Nox, or
  pre-commit unless later evidence shows lightweight reconciliation is
  insufficient.
- broad formatting cleanup unrelated to reconciliation.
- manual code rewrapping to satisfy Black.

## Acceptance Criteria for Planning Completion

- LRH project control artifacts document a dedicated reconciliation workstream.
- Follow-on implementation PR boundaries are explicit.
- Evidence expectations for environment mismatch claims are explicit.

## Follow-on Implementation Boundaries (for future PRs)

Future implementation PRs for this workstream should remain narrow and preferably
land in sequence:

1. version-policy and script/CI parity updates
2. diagnostics/evidence capture improvements
3. targeted fixes for verified drift cases

Each PR should demonstrate the invariant against concrete evidence from canonical
commands.
