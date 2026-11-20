---
resolution: null
blocked_reason: null
blocked: false
id: WI-LRH-DURABLE-MANUAL-RUN-STATE
title: Define and implement durable manual run state
type: deliverable
status: proposed
owner: anthony
contributors: []
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-EXECUTION-FRAMEWORK
related_design:
  - project/design/execution_framework_mvp.md
  - project/roadmap/roadmap.md
depends_on:
  - WI-LRH-SERVE-SAFE-DEFAULT-MVP
  - WI-EXECUTION-READINESS-SCHEMA
  - WI-RUN-PACKET-DRY-RUN
  - WI-RUN-REPORT-MVP
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - write_docs
  - add_cli_command
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - publish_package
  - run_lrh_agentic
  - implement_observation_adapters
  - implement_branch_containment
  - implement_branch_mutation
  - implement_pr_creation
  - implement_merge_release_automation
  - implement_backend_adapters
acceptance:
  - "The durable manual-run contract is documented for project/runs/<RUN-ID>/, including packet.yaml, state.yaml, events.jsonl, prompts/, evidence/, and report.md."
  - "Manual lifecycle states and explicit human-approved update paths are defined and validated, including recovery/resume semantics."
  - "Run artifacts reuse the existing execution-readiness, run-packet, run-report, and shared project-state contracts rather than inventing parallel planning semantics."
  - "The implementation preserves parity between manual runs and future automated runs without adding autonomous dispatch or mutation authority."
  - "Unit tests cover artifact creation, validation, lifecycle transitions, event durability, malformed or incomplete runs, and safe non-mutation behavior."
  - "lrh validate and the canonical formatting, lint, and test commands pass with 0 validation errors."
required_evidence:
  - code_diff
  - manual_review
  - lrh_validate
  - test_output
  - validation_output
artifacts_expected:
  - project/runs/<RUN-ID>/packet.yaml
  - project/runs/<RUN-ID>/state.yaml
  - project/runs/<RUN-ID>/events.jsonl
  - project/runs/<RUN-ID>/prompts/
  - project/runs/<RUN-ID>/evidence/
  - project/runs/<RUN-ID>/report.md
  - documentation
  - tests
---

# Define and implement durable manual run state

## Summary

Define and implement LRH's first durable manual-run state package so human-controlled runs have a stable, auditable artifact shape that future automated runs can reuse.

## Problem / Context

The shared project-state APIs, execution-readiness metadata, dry-run packet renderer, run-report renderer, and safe-default `lrh serve` workbench are complete. The repository's current focus identifies durable manual run state as the next implementation package, but no dedicated Layer 2 work item currently owns it. This item closes that planning gap while keeping observation, autonomous dispatch, branch mutation, PR automation, and backend integration deferred.

### Duplication search

- In-repo: Related design and handoff artifacts exist in `project/design/execution_framework_mvp.md`, `project/workstreams/proposed/WS-EXECUTION-FRAMEWORK.md`, and the resolved `WI-LRH-SERVE-SAFE-DEFAULT-MVP`; no existing dedicated Layer 2 work item was found.
- Sibling repos: None identified.
- External libraries: None identified; this is an LRH control-artifact contract and lifecycle problem.
- Recommendation: Proceed with a dedicated work item.

### Demand search

- Work items: No proposed work item with this dedicated scope was found.
- Proposals: No separate proposed proposal for this exact Layer 2 package was found.
- Backlog: The execution-framework design and roadmap explicitly request this package.
- Recommendation: No closure required; this work item formalizes the existing demand.

## Scope

- Define the durable manual-run directory and artifact contracts under `project/runs/<RUN-ID>/`.
- Implement explicit, human-controlled lifecycle and event updates.
- Reuse existing readiness, packet, report, and project-state semantics.
- Add validation, tests, and documentation for safe manual operation.

## Required Changes

1. Define the schema and invariants for `packet.yaml`, `state.yaml`, `events.jsonl`, prompt/evidence directories, and `report.md`.
2. Add the smallest LRH model, loader, validator, or CLI surface needed to create and inspect manual run artifacts.
3. Define lifecycle transitions, append-only event handling, malformed-state behavior, and recovery/resume semantics.
4. Ensure explicit human action is required for state-changing updates; read-only inspection and validation must not mutate runs.
5. Add documentation describing manual-run parity with future automated runs.
6. Add unit and boundary tests for valid, incomplete, malformed, and non-mutating cases.
7. Preserve the deferred boundary for observation adapters, autonomous dispatch, branch/PR mutation, stabilization loops, release automation, and backend adapters.

## Non-Goals

- Do not add autonomous `lrh run` execution.
- Do not dispatch agents or connect agent backends.
- Do not observe GitHub, CI, PRs, or review state.
- Do not create or mutate branches, PRs, merges, releases, or published artifacts.
- Do not implement branch containment, stabilization loops, MCP bridges, telemetry, or secrets-management behavior.
- Do not redesign the already-landed serve/workbench package.

## Acceptance Criteria

- The run-artifact layout and schema are documented and validated.
- Manual lifecycle transitions and explicit update paths work deterministically.
- Existing readiness, packet, report, and shared-state contracts are reused.
- Manual run artifacts are durable, auditable, recoverable, and safe by default.
- Tests cover successful, malformed, incomplete, recovery, and non-mutation paths.
- Canonical validation passes with 0 errors.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test --log`
- `PYTHONPATH=src python -m lrh.cli.main validate`
- `git diff --check`

## Risk Notes

- A new run schema could accidentally duplicate execution records or work-item semantics; the implementation must clearly separate run state from prompt execution history.
- Automatic writes from `lrh serve` would violate the safe-default boundary; all writes must be explicit.
- Over-designing future automation could make the manual contract unstable; the first slice should remain backend-neutral and human-controlled.
- The governing workstream is still marked proposed, so its activation and ownership should be reconciled when this item is accepted.
