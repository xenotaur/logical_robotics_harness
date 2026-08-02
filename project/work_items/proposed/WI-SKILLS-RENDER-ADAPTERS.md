---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-RENDER-ADAPTERS
title: Add Claude and Codex skill render adapters
type: deliverable
status: proposed
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
  - project/design/proposals/proposed/lrh-skills-target-aware-install/backlog.md
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
  - Claude and Codex install paths render through explicit target adapters
  - Codex installs emit or preserve `agents/openai.yaml` when needed
  - Claude `disable-model-invocation: true` is translated to Codex manual-only invocation policy
  - Unsupported Claude-only metadata is stripped, translated, or reported deliberately
  - lrh validate reports 0 errors
required_evidence:
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/skills/installer.py
  - tests/skills_installer_test.py
---

# Add Claude and Codex skill render adapters

## Summary

Split skill output generation into target-specific render adapters so Claude
and Codex installs can preserve platform-specific semantics without divergent
hand-maintained skill trees.

## Problem / Context

Direct copying is enough for the first Codex install slice, but it cannot
preserve all intended behavior. Manual-only invocation policy and unsupported
Claude UI metadata require explicit Codex handling.

## Scope

- Add Claude and Codex renderer abstractions.
- Translate manual-only invocation policy into Codex `agents/openai.yaml`.
- Report or remove unsupported metadata intentionally.
- Use the proposal-local backlog as test input for Codex compatibility cases.

## Non-Goals

- Does not perform all body-prose neutralization.
- Does not implement ChatGPT export.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
