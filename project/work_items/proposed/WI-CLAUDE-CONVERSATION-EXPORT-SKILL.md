---
resolution: null
blocked_reason: null
blocked: false
id: WI-CLAUDE-CONVERSATION-EXPORT-SKILL
title: Implement lrh-export-claude agent skill
type: deliverable
status: proposed
owner: null
contributors: []
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design:
  - project/design/proposals/proposed/lrh-claude-conversation-exporter/00_proposal.md
depends_on:
  - WI-CLAUDE-CONVERSATION-EXPORT-CLI
blocked_by: []
expected_actions:
  - create_file
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - "src/lrh/skills/lrh-export-claude/SKILL.md exists with valid frontmatter"
  - "Skill includes a mandatory confirm-before-write gate before any durable archive write"
  - "Skill runs lrh conversation inspect-export with source-hash verification and reports metadata only"
  - "CLAUDE.md ## Skills index includes /lrh-export-claude"
  - "lrh validate reports 0 errors"
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-export-claude/SKILL.md
  - .claude/skills/lrh-export-claude/SKILL.md
  - .agents/skills/lrh-export-claude/SKILL.md
  - CLAUDE.md
---

# WI-CLAUDE-CONVERSATION-EXPORT-SKILL: Implement lrh-export-claude agent skill

## Summary

Implement Tranche 3 of `PROP-LRH-CLAUDE-CONVERSATION-EXPORTER`: a `/lrh-export-claude` skill wrapping `lrh conversation export-claude-session`, following `lrh-codex-export`'s confirm-before-write and metadata-only-report pattern.

## Problem / Context

`WI-CLAUDE-CONVERSATION-EXPORT-CLI` provides the CLI subcommand but no agent-facing skill wrapper. `/lrh-antigravity-export` and `/lrh-codex-export` are the direct precedents for how LRH exposes conversation exporters as skills.

### Duplication search
- In-repo: No `lrh-export-claude` skill directory exists. `src/lrh/skills/lrh-codex-export/SKILL.md` (confirm-before-write gate pattern) and `src/lrh/skills/lrh-antigravity-export/SKILL.md` (metadata-only report pattern) are the direct precedents.
- Sibling repos: None identified.
- External libraries: Not applicable.
- Recommendation: Proceed.

### Demand search
- Work items: `WI-CLAUDE-CONVERSATION-EXPORT-CLI` (dependency).
- Proposals: `PROP-LRH-CLAUDE-CONVERSATION-EXPORTER` Implementation Plan item 3.
- Backlog: No matching entries.
- Recommendation: No action; implements the proposal directly.

**Naming note:** the skill is named `lrh-export-claude` (not `lrh-claude-export`)
per `PROP-LRH-CLAUDE-CONVERSATION-EXPORTER`'s Design Decision 9, anticipating
the long-deferred umbrella dispatcher `/lrh-export`
(`project/design/backlog.md`, "Status: Tracked, not yet designed"). The two
already-shipped siblings, `lrh-antigravity-export` and `lrh-codex-export`,
keep their current names — this item does not rename them.

## Scope

- Create `src/lrh/skills/lrh-export-claude/SKILL.md`.
- Add the `CLAUDE.md` `## Skills` index entry per the `lrh-create-skill` pattern.
- Excludes any change to the underlying CLI or Python API.

## Required Changes

1. Create `src/lrh/skills/lrh-export-claude/SKILL.md` with frontmatter (`name`, `description`, `when_to_use`, `argument-hint`) following `lrh-codex-export/SKILL.md:1-17`'s shape.
2. Document inputs mirroring `lrh-codex-export/SKILL.md`'s Inputs section, adapted for `--transcript-path` / `--session-id` / `--latest`.
3. Include a **mandatory confirm-before-write gate** before any durable archive write, since the archive is durable-by-default (proposal Design Decisions 6-7) — following `lrh-codex-export/SKILL.md:144-160`'s pattern exactly, including the rationale note that `when_to_use` narrows auto-trigger but the actual write-protection is the explicit confirm gate.
4. Run the export with a restrictive umask (`umask 077`), mirroring `lrh-codex-export/SKILL.md:168-174`.
5. Run `lrh conversation inspect-export <output_path> --source <transcript_file>` and confirm exit code 0 and `Source hash: match`, mirroring `lrh-antigravity-export/SKILL.md:74-82`.
6. Report metadata-only terminal status — output path, source ID, source SHA-256, privacy, sensitivity, warning count — without printing raw transcript body text to stdout or stderr.
7. Add a `/lrh-export-claude` entry to `CLAUDE.md`'s `## Skills` index, following the existing `/lrh-antigravity-export` and `/lrh-codex-export` entry format.
8. Verify rendered installs (`.claude/skills/lrh-export-claude/`, `.agents/skills/lrh-export-claude/`) are up to date per the `lrh-create-skill` distribution pattern.

## Non-Goals

- Does not implement the `SessionEnd` hook-based automatic-capture mechanism — explicitly out of scope per the proposal's Non-Goals.
- Does not modify `src/lrh/cli/main.py` or `src/lrh/conversations/claude_export.py` — those are `WI-CLAUDE-CONVERSATION-EXPORT-API`/`-CLI`.

## Acceptance Criteria

- `src/lrh/skills/lrh-export-claude/SKILL.md` exists with valid frontmatter.
- The skill includes a mandatory confirm-before-write gate before any durable archive write.
- The skill runs `lrh conversation inspect-export` with source-hash verification and reports metadata only.
- `CLAUDE.md`'s `## Skills` index includes `/lrh-export-claude`.
- `lrh validate` reports 0 errors.

## Validation

- `lrh validate`
- `lrh skills check --target claude --local`
- `lrh skills status --target codex --local`
