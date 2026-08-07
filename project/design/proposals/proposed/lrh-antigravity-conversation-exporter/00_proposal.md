---
id: PROP-LRH-ANTIGRAVITY-CONVERSATION-EXPORTER
type: design_proposal
title: LRH Antigravity Conversation Exporter Design Proposal
status: proposed
created_on: 2026-08-07
updated_on: 2026-08-07
implementation_status: not_started
related_design:
  - project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md
  - project/design/proposals/adopted/lrh-codex-conversation-exporter/00_proposal.md
supersedes: []
superseded_by: null
---

# LRH Antigravity Conversation Exporter Design Proposal

## Summary

This proposal defines the design and implementation model for exporting Google Antigravity agent conversation sessions into private-by-default, non-authoritative Markdown transcript artifacts backed by structured `ConversationExportManifest` frontmatter metadata and heuristic sensitivity scanning.

The exporter is delivered across three modular tranches: (1) a core Python API in `src/lrh/conversations/antigravity_export.py`, (2) a CLI subcommand `lrh conversation export-antigravity-session` in `src/lrh/cli/main.py`, and (3) an Antigravity agent skill package in `src/lrh/skills/lrh-antigravity-export/`.

## Background / Motivation

AI-assisted development sessions conducted within Google Antigravity generate context, tool executions, and step-by-step reasoning logs. Currently, Antigravity lacks a built-in `/export` skill to archive or dump session transcripts for inspection, auditing, or provenance tracking.

Following the design established by the Codex conversation exporter (`PROP-LRH-CODEX-CONVERSATION-EXPORTER`) and the broader storage interop framework (`PROP-LRH-CONVERSATIONS-STORAGE-INTEROP`), LRH should support parsing Antigravity session trajectories stored on disk (`<appDataDir>/brain/<conversation-id>/.system_generated/logs/transcript.jsonl`) into standard Markdown export artifacts without treating raw conversation history as authoritative project state.

## Prior Art Check

### Duplication search
- In-repo: Found existing conversation export adapters for ChatGPT PDF (`src/lrh/conversations/pdf_import.py`) and explicit Codex files (`src/lrh/conversations/codex_file_export.py`). No existing Antigravity session exporter implementation found in `src/lrh/` or `project/`.
- Sibling repos: None identified.
- External libraries: Google Antigravity SDK (`google-antigravity`) provides session persistence via `LocalAgentConfig(save_dir=..., conversation_id=...)`, but no LRH-compliant Markdown export tool.
- Recommendation: Proceed — implement `src/lrh/conversations/antigravity_export.py`.

### Demand search
- Work items: Satisfies Phase 3 (conversation import/export) of `PROP-LRH-CONVERSATIONS-STORAGE-INTEROP`.
- Proposals: Aligns with `PROP-LRH-CONVERSATIONS-STORAGE-INTEROP` and `PROP-LRH-CODEX-CONVERSATION-EXPORTER`.
- Backlog: No matching entries.
- Recommendation: Proceed; link to `PROP-LRH-CONVERSATIONS-STORAGE-INTEROP`.

## Design Decisions

1. **3-Tranche Staging**:
   - Tranche 1: Core Python Exporter API (`src/lrh/conversations/antigravity_export.py`).
   - Tranche 2: CLI Subcommand (`lrh conversation export-antigravity-session`).
   - Tranche 3: Antigravity Agent Skill (`src/lrh/skills/lrh-antigravity-export/SKILL.md`).
2. **Data Source & Extraction**: Direct parsing of local `transcript.jsonl` files (`<appDataDir>/brain/<conversation-id>/.system_generated/logs/transcript.jsonl`), enabling fast, hermetic, offline exports without requiring active backend daemons.
3. **Manifest & Safety**: Output artifacts use standard `ConversationExportManifest` frontmatter (`privacy: private`, `authority: non_authoritative_context`, `source_tool: antigravity`, `source_adapter: antigravity_transcript_jsonl`), with automatic `lrh.conversations.sensitivity` pre-write scanning.
4. **Resilience to Incomplete Sessions**: Gracefully handle partial trailing lines when exporting an actively running session by recording an `incomplete_trailing_step_ignored` manifest warning.

## Non-Goals

- Do not modify Antigravity internal database schemas or daemon runtimes.
- Do not make exported transcripts authoritative project state.
- Do not automatically promote transcript text into work items, design decisions, or evidence without human review.

## Implementation Plan

1. **Tranche 1**: Implement `AntigravityExport` dataclass and parsing functions in `src/lrh/conversations/antigravity_export.py`; add hermetic unit tests in `tests/conversations_tests/antigravity_export_test.py`.
2. **Tranche 2**: Register `export-antigravity-session` subcommand under `lrh conversation` in `src/lrh/cli/main.py`.
3. **Tranche 3**: Create Antigravity Skill `lrh-antigravity-export` in `src/lrh/skills/lrh-antigravity-export/`.
