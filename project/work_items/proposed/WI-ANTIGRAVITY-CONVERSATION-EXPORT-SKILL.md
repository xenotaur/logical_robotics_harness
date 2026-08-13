---
id: WI-ANTIGRAVITY-CONVERSATION-EXPORT-SKILL
title: Implement native Antigravity export skill package
type: deliverable
status: proposed
blocked: false
blocked_reason: null
resolution: null
related_workstreams:
  - WS-ANTIGRAVITY-CONVERSATION-EXPORT
depends_on:
  - WI-ANTIGRAVITY-CONVERSATION-EXPORT-CLI
blocked_by: []
artifacts_expected:
  - src/lrh/skills/lrh-antigravity-export/SKILL.md
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - Skill file src/lrh/skills/lrh-antigravity-export/SKILL.md exists with valid YAML frontmatter.
  - Documents procedure for extracting transcriptPath metadata and executing lrh conversation export-antigravity-session --transcript-path PATH.
  - Passes lrh validate cleanly.
---

# WI-ANTIGRAVITY-CONVERSATION-EXPORT-SKILL: Implement native Antigravity export skill package

## Summary

Implement Tranche 3 of the Antigravity conversation session exporter: create the `lrh-antigravity-export` agent skill package in `src/lrh/skills/lrh-antigravity-export/SKILL.md` to provide a native `/export` capability inside Google Antigravity sessions.

## Problem / Context

Google Antigravity does not ship with a native `/export` skill. Providing an LRH skill allows agents operating in Antigravity to dump session transcripts directly into private Markdown artifacts using the session's documented `transcriptPath`.

### Prior Art Check
- Duplication search: No existing `lrh-antigravity-export` skill in `src/lrh/skills/`.
- Demand search: Fulfills Tranche 3 of `PROP-LRH-ANTIGRAVITY-CONVERSATION-EXPORTER` and `WS-ANTIGRAVITY-CONVERSATION-EXPORT`.

## Scope

### Included
- `src/lrh/skills/lrh-antigravity-export/SKILL.md`.

### Excluded
- Python library code (covered by WI-1 and WI-2).

## Required Changes

- Create `src/lrh/skills/lrh-antigravity-export/SKILL.md`.
- Add YAML frontmatter with `name: lrh-antigravity-export`, `description`, `when_to_use`, `argument-hint`.
- Provide step-by-step procedure for extracting `transcriptPath` from Antigravity session metadata, executing `lrh conversation export-antigravity-session --transcript-path PATH --out OUTPUT.md`, and reporting output path.

## Non-Goals

- Do not embed python parsing code directly inside the SKILL.md body (delegate to CLI).

## Acceptance Criteria

- `src/lrh/skills/lrh-antigravity-export/SKILL.md` exists and contains valid frontmatter.
- `lrh validate` reports 0 errors.

## Validation

- `lrh validate`
