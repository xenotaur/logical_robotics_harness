---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-BODY-PROSE-NEUTRALIZATION
title: Neutralize Claude-specific LRH skill body prose for Codex
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
  - WI-SKILLS-RENDER-ADAPTERS
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - Proposal-local Codex compatibility backlog is reviewed and updated
  - Claude-specific body prose is rewritten or deliberately retained with rationale
  - Codex-installed skills no longer instruct Codex to record itself as Claude
  - Invocation examples are agent-neutral or target-aware where practical
  - lrh validate reports 0 errors
required_evidence:
  - lrh_validate
  - manual_review
artifacts_expected:
  - src/lrh/skills
  - .claude/skills
  - project/design/proposals/proposed/lrh-skills-target-aware-install/backlog.md
---

# Neutralize Claude-specific LRH skill body prose for Codex

## Summary

Burn down Claude-specific instructions in LRH skill bodies so skills installed
for Codex behave as first-class Codex workflows rather than copied Claude
prompts.

## Problem / Context

The proposal accepts direct-copy Codex output as an interim slice, but current
skill bodies contain Claude Code provenance, slash-command, and mirror-target
assumptions. Those issues should be fixed deliberately after target-aware
installation and render adapters are in place.

## Scope

- Review every proposal-local backlog entry.
- Rewrite or render Claude-specific body prose where needed.
- Preserve Claude usability in `.claude/skills/`.
- Update backlog status as issues are burned down.

## Non-Goals

- Does not change core install target mechanics.
- Does not implement ChatGPT export.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test` when source behavior changes
- `lrh validate`
