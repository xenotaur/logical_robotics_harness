---
resolution: null
blocked_reason: null
blocked: false
id: WI-LRH-EXPORT-DISPATCHER
title: "Add the /lrh-export dispatcher skill over lrh-export-claude, lrh-export-codex and lrh-export-antigravity"
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
  - WI-EXPORT-SKILL-FAMILY-RENAME
blocked_by: []
expected_actions:
  - create_file
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - weaken_human_gate
  - print_transcript_text
  - skills_install_force
acceptance:
  - "src/lrh/skills/lrh-export/SKILL.md selects the vendor from an explicit first argument (claude, codex or antigravity) first, then from CLAUDE_CODE_SESSION_ID or CODEX_THREAD_ID (plus an Antigravity signal only if WI-ANTIGRAVITY-SESSION-ID-INVESTIGATION found one), and asks the user when no signal is present or several are"
  - "After selecting the vendor, the dispatcher runs the variant skill's own steps inline, passing the remaining arguments through unchanged; it adds no write step, archive default or confirm gate of its own, and the variant's confirm gate still fires"
  - "The dispatcher's when_to_use restricts invocation to an explicit user request to export, matching its variants, and never triggers proactively"
  - "The skill is installed to all three targets without --force, and CLAUDE.md lists /lrh-export"
  - "lrh validate reports 0 errors and scripts/test, scripts/lint and scripts/format --check --diff pass"
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-export/SKILL.md
  - src/lrh/skills/lrh-export/agents/openai.yaml
  - .claude/skills/lrh-export/
  - .agents/skills/lrh-export/
  - .gemini/plugins/lrh/skills/lrh-export/
  - CLAUDE.md
---

# WI-LRH-EXPORT-DISPATCHER: Add the /lrh-export dispatcher

## Summary

Add `/lrh-export`, a delegating dispatcher (`PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES`
Decision 2). It works out which agent environment the session is in, then
runs the matching `lrh-export-<vendor>` skill. Users get one command for
transcript export regardless of which agent they are using.

## Problem / Context

`/lrh-export` has been the documented name for a vendor-aware export command
since 2026-08-07:

- the design backlog;
- `PROP-LRH-CODEX-APP-SERVER-CONVERSATION-EXPORT` Implementation Plan item 3;
- open PR #542's Decision 1.

It was deferred until each vendor had an exporter with a durable archive
default. All three do now. Once `WI-EXPORT-SKILL-FAMILY-RENAME` lands, every
variant shares the `lrh-export-` prefix.

The dispatcher delegates, following the same pattern `/lrh-execute` uses to
run `/lrh-implement`: it reads the variant's `SKILL.md` and carries out its
steps. The variant's resolution rules, confirm-before-write gate and
metadata-only reporting all stay in force. The dispatcher must not guess the
vendor: a wrong guess writes a permanent archive copy of the wrong session.

### Duplication search
- In-repo: Related: the three `lrh-export-<vendor>` skills. Open PR #542
  proposes the same dispatcher shape as part of a wider archive-layout
  design. No dispatcher exists.
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed.

### Demand search
- Work items: None found.
- Proposals: `PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES` Decision 2;
  `PROP-LRH-CODEX-APP-SERVER-CONVERSATION-EXPORT` Implementation Plan item 3.
- Backlog: "Generalize conversation export manifests beyond Codex before
  `/lrh-export`".
- Recommendation: No action. `WI-EXPORT-SESSION-ID-DOCS` resolves the backlog
  entry.

## Scope

- Add the dispatcher skill, installed to all three targets, and add it to
  `CLAUDE.md`.

## Required Changes

1. Create `src/lrh/skills/lrh-export/SKILL.md` and `agents/openai.yaml`. The
   skill must:
   - take an optional first argument, `claude`, `codex` or `antigravity`, and
     pass any remaining arguments through;
   - pick the vendor in this order:
     1. the explicit argument;
     2. `CLAUDE_CODE_SESSION_ID`, meaning Claude;
     3. `CODEX_THREAD_ID`, meaning Codex;
     4. the Antigravity signal, only if the investigation appendix
        documents one;
     5. otherwise, ask the user;
   - ask the user when more than one environment signal is present, and never
     pick one silently;
   - state the selected vendor, then carry out `lrh-export-<vendor>`'s steps
     inline;
   - use a `when_to_use` that matches the variants: only on an explicit user
     request to export, never proactively.
2. Install it to all three targets, one skill at a time.
3. Add `/lrh-export` to `CLAUDE.md`.

## Non-Goals

- Does not change any variant's behavior, gates or archive paths.
- Does not implement PR #542's archive-layout or sorter decisions.
- Does not add the `/lrh-session-id` dispatcher.

## Acceptance Criteria

- The dispatcher picks the vendor from the argument, then the environment,
  then by asking. It asks when signals conflict.
- It runs the variant inline with arguments passed through and adds no gate
  or write step of its own. The variant's confirm gate still fires.
- `when_to_use` limits it to explicit export requests.
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

## Risk Notes

- If both the Claude and Codex variables are set (for example, Claude Code
  running in a Codex-hosted terminal), the dispatcher must ask. Dogfood this
  case if possible (proposal Open Question 3).
