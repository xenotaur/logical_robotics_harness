---
resolution: null
blocked_reason: null
blocked: false
id: WI-LRH-SESSION-ID-DISPATCHER
title: "Add the /lrh-session-id dispatcher skill over the lrh-session-id-<vendor> variants"
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
  - WS-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES
related_design:
  - project/design/proposals/proposed/lrh-export-session-id-skill-families/00_proposal.md
depends_on:
  - WI-SESSION-ID-CODEX-SKILL-RENAME
  - WI-SKILLS-LRH-CLAUDE-SESSION
blocked_by: []
expected_actions:
  - run_tests
  - create_file
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - export_transcript_content
  - print_transcript_text
  - skills_install_force
acceptance:
  - "src/lrh/skills/lrh-session-id/SKILL.md selects the vendor from an explicit first argument first, then from the environment, and asks when no signal is present or several are, using the same order as /lrh-export"
  - "After selecting the vendor, the dispatcher runs lrh-session-id-<vendor>'s steps inline with the remaining arguments passed through; it never reads or exports transcript content"
  - "When the selected variant does not exist (Antigravity before WI-ANTIGRAVITY-SESSION-ID-RESOLVER ships), the dispatcher reports the vendor as unsupported and session_transcript as pending, and does not guess a pointer"
  - "The skill is installed to all three targets without --force, and CLAUDE.md lists /lrh-session-id"
  - "lrh validate reports 0 errors and scripts/test, scripts/lint and scripts/format --check --diff pass"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/skills/lrh-session-id/SKILL.md
  - src/lrh/skills/lrh-session-id/agents/openai.yaml
  - .claude/skills/lrh-session-id/
  - .agents/skills/lrh-session-id/
  - .gemini/plugins/lrh/skills/lrh-session-id/
  - CLAUDE.md
---

# WI-LRH-SESSION-ID-DISPATCHER: Add the /lrh-session-id dispatcher

## Summary

Add `/lrh-session-id`, a delegating dispatcher
(`PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES` Decision 2). It works out which
agent environment the session is in and runs the matching
`lrh-session-id-<vendor>` skill. The result is one command that reports the
`session_transcript:` pointer an execution record needs, without exporting
anything.

## Problem / Context

Session pointers are written into every execution record, and today each
caller must know which vendor skill to use. `/lrh-closeout`, `/lrh-land` and
`/lrh-implement` each restate vendor-specific resolution. A single entry point
lets callers, and users, ask for "this session's ID" and get the right pointer
in each environment.

Unlike `/lrh-export`, this dispatcher is metadata-only. Like
`lrh-codex-session` today, it may be called from other skills without an
explicit user request.

This item depends on `WI-SESSION-ID-CODEX-SKILL-RENAME` and
`WI-SKILLS-LRH-CLAUDE-SESSION`, so the Claude and Codex variants exist under
their final names. The Antigravity variant may ship later
(`WI-ANTIGRAVITY-SESSION-ID-RESOLVER`). Until it does, the dispatcher must
report that vendor as unsupported rather than guess.

Routing `/lrh-closeout`, `/lrh-land` and `/lrh-implement` through this
dispatcher, instead of through the per-vendor skills, is left to a follow-up.
`WI-SKILLS-LRH-CLAUDE-SESSION` already routes the Claude case.

### Duplication search
- In-repo: Related: `lrh-codex-session` (to become `lrh-session-id-codex`) and
  the planned `lrh-session-id-claude`. No dispatcher exists.
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed.

### Demand search
- Work items: None found.
- Proposals: `PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES` Decision 2.
- Backlog: No matching entries.
- Recommendation: No action.

## Scope

- Add the dispatcher skill, installed to all three targets, and add it to
  `CLAUDE.md`.

## Required Changes

1. Create `src/lrh/skills/lrh-session-id/SKILL.md` and `agents/openai.yaml`.
   The skill must:
   - pick the vendor using the same order and ambiguity rule as
     `/lrh-export`;
   - carry out `lrh-session-id-<vendor>`'s steps inline, passing remaining
     arguments through;
   - when the variant does not exist, report the vendor as unsupported and
     `session_transcript: pending`;
   - include safety rules: no transcript reads, no exports, never call
     `export_transcript`.
2. Install it to all three targets, one skill at a time.
3. Add `/lrh-session-id` to `CLAUDE.md`.

## Non-Goals

- Does not change any variant's resolution logic or pointer format.
- Does not move `/lrh-closeout`, `/lrh-land` or `/lrh-implement` onto the
  dispatcher.
- Does not add the Antigravity variant.

## Acceptance Criteria

- The dispatcher picks the vendor from the argument, then the environment,
  then by asking. It asks when signals conflict.
- It runs the variant inline and never touches transcript content.
- A missing variant is reported as unsupported with `pending`, not guessed.
- It is installed to all three targets and listed in `CLAUDE.md`.
- `lrh validate` reports 0 errors, and tests, lint and format checks pass.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh skills check --target claude --local`
- `lrh skills status --target codex --local`
- `lrh skills status --target antigravity --local`
