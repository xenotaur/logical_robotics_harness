---
resolution: completed
blocked_reason: null
blocked: false
id: WI-CI-PLAYBOOK
title: Create CI setup and debugging playbook
type: deliverable
status: resolved
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-CI-CAPABILITY-SCAFFOLDING
related_design:
  - project/design/proposals/proposed/ci-capability-scaffolding.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - create_report
forbidden_actions:
  - add_ci_workflow_template
  - implement_agent_skill
  - introduce_tool
acceptance:
  - CI setup and debugging playbook exists at docs/project-setup/ci.md
  - playbook covers project-family discovery, canonical commands, setup versus validation, tool reproducibility, GitHub Actions design, workflow YAML guardrails, evidence, minimal acceptance, and template-fragment guidance
  - nearby documentation and control-plane artifacts link to the playbook
  - execution record exists for the implementation prompt
required_evidence:
  - manual_review
  - validation_output
artifacts_expected:
  - documentation
  - execution_record
---

## Summary

Create the human-facing CI setup and debugging playbook for the CI capability scaffolding workstream.

## Problem / Context

The CI capability scaffolding proposal calls for a staged strategy. The first substantive phase is a practical playbook that captures LRH's development-toolchain reconciliation lessons and makes them reusable across heterogeneous repositories before request-template, skill, or reusable-fragment work proceeds.

## Required Changes

- Add `docs/project-setup/ci.md` as a concise how-to guide for humans and agents.
- Link the playbook from relevant documentation indexes and control-plane artifacts.
- Preserve this PR's scope as documentation/control-plane work only.
- Add an execution record for the implementation prompt.

## Non-Goals

- Do not update CI request templates except for links if needed.
- Do not implement an Agent Skill.
- Do not add CI workflow templates or reusable workflow fragments.
- Do not introduce new tools.
- Do not modify LRH's existing CI workflows.

## Acceptance Criteria

- CI setup and debugging playbook exists at `docs/project-setup/ci.md`.
- Playbook covers project-family discovery, existing-command inventory, canonical setup/version/format/lint/test/workflow-check commands, setup-versus-validation separation, tool-version reproducibility, GitHub Actions design, workflow YAML guardrails, evidence-based debugging, minimal CI acceptance criteria, and when to use templates or fragments.
- Nearby documentation and control-plane artifacts link to the playbook.
- Execution record exists for `PROMPT(WI-CI-PLAYBOOK:CREATE_CI_PROJECT_SETUP_PLAYBOOK)[2026-05-14T00:15:00-04:00]`.

## Validation Commands

- `scripts/version tools`
- `scripts/check-workflows`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-CI-CAPABILITY-SCAFFOLDING.md`
- Design proposal: `project/design/proposals/proposed/ci-capability-scaffolding.md`

## Risk Notes

- The playbook could become too generic if it stops referencing concrete command categories and evidence expectations.
- CI request-template, Agent Skill, and workflow-template work should remain follow-up phases until the playbook has been dogfooded.
