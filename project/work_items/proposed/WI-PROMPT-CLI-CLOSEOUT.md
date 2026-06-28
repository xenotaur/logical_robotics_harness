---
resolution: null
blocked_reason: null
blocked: false
id: WI-PROMPT-CLI-CLOSEOUT
title: Implement lrh prompt update-execution CLI command (Phase 2)
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-SKILLS-CLOSEOUT
related_design:
  - project/design/proposals/adopted/lrh-closeout/00_proposal.md
  - project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md
depends_on:
  - WI-SKILLS-LRH-CLOSEOUT
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
acceptance: []
required_evidence:
  - lrh_validate
artifacts_expected: []
---

## Summary

Implement `lrh prompt update-execution` — the CLI subcommand specified in
PROP-LRH-CLOSEOUT Decision 3 — and upgrade `/lrh-closeout` Step 5 from
edit-in-place to call this command. This is Phase 2 of `WS-SKILLS-CLOSEOUT`;
Phase 1 (`WI-SKILLS-LRH-CLOSEOUT`) has already landed.

## Problem / Context

TODO: flesh out with `lrh request ready-work-item`. Reference:
PROP-LRH-CLOSEOUT Decision 3 (CLI interface spec) and Decision 5 (Step 5
upgrade path). The 4-field interface is already specified:
`--execution-id`, `--status`, `--pr`, `--commit`, `--session-transcript`.

## Required Changes

TODO: flesh out. Key changes expected:
- Implement `lrh prompt update-execution` in `src/lrh/prompts/` (or equivalent)
- Update `src/lrh/skills/lrh-closeout/SKILL.md` Step 5 to call the CLI
- Update `src/lrh/skills/lrh-implement/references/execution-session-reference.md`
  with the new command syntax
- Mirror skill changes to `.claude/skills/lrh-closeout/`

## Non-Goals

- Does not implement `lrh closeout` as a top-level command (per PROP-LRH-CLOSEOUT
  Decision 3 — the skill is the interface; CLI is scoped to record mutation only)
- Does not change the skill's external step structure or reference files

## Acceptance Criteria

TODO: flesh out with `lrh request ready-work-item`.

## Validation

- `lrh validate`
- `diff -r src/lrh/skills/lrh-closeout/ .claude/skills/lrh-closeout/`
- `scripts/version tools` / `scripts/test` if Python changes involved
