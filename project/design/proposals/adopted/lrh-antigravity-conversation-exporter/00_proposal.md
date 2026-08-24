---
id: PROP-LRH-ANTIGRAVITY-CONVERSATION-EXPORTER
type: design_proposal
title: LRH Antigravity Conversation Exporter Design Proposal
status: adopted
created_on: 2026-08-07
updated_on: 2026-08-23
implementation_status: implemented
implemented_by:
  - WI-ANTIGRAVITY-CONVERSATION-EXPORT-API
  - WI-ANTIGRAVITY-CONVERSATION-EXPORT-CLI
  - WI-ANTIGRAVITY-CONVERSATION-EXPORT-SKILL
related_design:
  - project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md
  - project/design/proposals/adopted/lrh-codex-conversation-exporter/00_proposal.md
supersedes: []
superseded_by: null
---

# LRH Antigravity Conversation Exporter Design Proposal

## Summary

This proposal defines the design and implementation model for exporting Google Antigravity agent conversation sessions into private-by-default, non-authoritative Markdown transcript artifacts backed by generalized `ConversationExportManifest` frontmatter metadata and heuristic sensitivity scanning.

The exporter is delivered across three modular tranches: (1) a core Python API in `src/lrh/conversations/antigravity_export.py`, (2) a CLI subcommand `lrh conversation export-antigravity-session` in `src/lrh/cli/main.py`, and (3) an Antigravity agent skill package in `src/lrh/skills/lrh-antigravity-export/`.

## Background / Motivation

AI-assisted development sessions conducted within Google Antigravity generate context, tool executions, and step-by-step reasoning logs. Antigravity hook metadata provides documented session pointers (`conversationId`, `transcriptPath`, `artifactDirectoryPath`), but currently lacks a built-in `/export` skill to archive or dump session transcripts for inspection, auditing, or provenance tracking.

Following the design established by the Codex conversation exporter (`PROP-LRH-CODEX-CONVERSATION-EXPORTER`) and the broader storage interop framework (`PROP-LRH-CONVERSATIONS-STORAGE-INTEROP`), LRH should support parsing Antigravity session trajectories stored on disk into standard Markdown export artifacts without treating raw conversation history as authoritative project state.

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

1. **Manifest Generalization Prerequisite**:
   - The current `ConversationExportManifest` (`src/lrh/conversations/export_manifest.py`) hardcodes `KIND = "lrh_codex_conversation_export"` and enforces `source_tool == "codex"`.
   - Prerequisite Step 0: Generalize `ConversationExportManifest` and `export_inspector.py` to support multi-source tools (e.g. `source_tool: antigravity`, `source_tool: codex`) and versioned manifest schema rules before Antigravity export generation.

2. **Primary Input via Documented `transcriptPath`**:
   - Antigravity hooks expose explicit `transcriptPath` pointers.
   - Primary CLI interface uses `--transcript-path PATH` (or positional `TRANSCRIPT_PATH` file path) as the foundational source route:
     `lrh conversation export-antigravity-session --transcript-path PATH --out EXPORT.md`
   - Retain `--conversation-id`, `--app-data-dir`, and `--latest` as optional discovery conveniences rather than the mandatory entry point.

3. **3-Tranche Staging**:
   - Tranche 1: Core Python Exporter API (`src/lrh/conversations/antigravity_export.py`).
   - Tranche 2: CLI Subcommand (`lrh conversation export-antigravity-session`).
   - Tranche 3: Antigravity Agent Skill (`src/lrh/skills/lrh-antigravity-export/SKILL.md`).

4. **Evidence / Dogfood Verification Gate**:
   - Conduct a private real-session spike/dogfood check against actual `transcriptPath` JSONL logs to verify real Antigravity step/event payloads before locking renderer item mapping functions.

5. **Manifest & Safety Standards**:
   - Output artifacts calculate `source_sha256`, `source_id`, and `transcript_statistics` (`byte_count`, `character_count`, `line_count`, `turn_count`, `message_count`).
   - Set `privacy: private` and `authority: non_authoritative_context`.
   - Run local heuristic sensitive content scanning (`lrh.conversations.sensitivity`) before writing output.
   - Enforce metadata-only terminal output by default (no printing of raw transcript bodies to stdout/stderr).
   - Ensure complete compatibility with `lrh conversation inspect-export`.

## Non-Goals

- Do not modify Antigravity internal database schemas or daemon runtimes.
- Do not make exported transcripts authoritative project state.
- Do not commit raw `transcript.jsonl` files to public repository state.
- Do not automatically promote transcript text into work items, design decisions, or evidence without human review.

## Implementation Plan

1. **Prerequisite Step 0**: Generalize `ConversationExportManifest` and `export_inspector.py` for multi-source tool compatibility (`source_tool: antigravity`).
2. **Dogfood Verification**: Inspect real Antigravity `transcriptPath` JSONL payloads to verify step types and tool execution schemas.
3. **Tranche 1**: Implement `AntigravityExport` dataclass and parsing functions in `src/lrh/conversations/antigravity_export.py`; add hermetic unit tests in `tests/conversations_tests/antigravity_export_test.py`.
4. **Tranche 2**: Register `export-antigravity-session` subcommand under `lrh conversation` in `src/lrh/cli/main.py`.
5. **Tranche 3**: Create Antigravity Skill `lrh-antigravity-export` in `src/lrh/skills/lrh-antigravity-export/`.
