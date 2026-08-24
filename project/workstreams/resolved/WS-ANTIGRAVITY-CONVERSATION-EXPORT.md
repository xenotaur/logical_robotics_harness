---
id: WS-ANTIGRAVITY-CONVERSATION-EXPORT
kind: planning_node
title: Antigravity Conversation Session Exporter
status: resolved
stage: closed
summary: "Orchestrates the 3-tranche implementation of the Antigravity conversation session exporter, spanning Python API library code, lrh conversation CLI integration, and a native Antigravity skill package."
related_design:
  - project/design/proposals/proposed/lrh-antigravity-conversation-exporter/00_proposal.md
  - project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md
work_items:
  - WI-ANTIGRAVITY-CONVERSATION-EXPORT-API
  - WI-ANTIGRAVITY-CONVERSATION-EXPORT-CLI
  - WI-ANTIGRAVITY-CONVERSATION-EXPORT-SKILL
exit_criteria:
  - 'ConversationExportManifest is generalized to support source_tool: antigravity and export_inspector.py passes updated manifest checks.'
  - Private real-session JSONL dogfood spike confirms observed Antigravity transcript event payload shapes.
  - Python API in src/lrh/conversations/antigravity_export.py parses Antigravity JSONL logs into Markdown artifacts with valid ConversationExportManifest frontmatter, source_sha256, source_id, and transcript_statistics, passing hermetic unit tests.
  - CLI subcommand lrh conversation export-antigravity-session accepts --transcript-path PATH as primary input, outputs metadata-only status, and passes integration tests.
  - Native Antigravity skill in src/lrh/skills/lrh-antigravity-export/ passes skill check and lrh validate cleanly.
---

# Antigravity Conversation Session Exporter Workstream

## Purpose

This workstream coordinates the 3-tranche implementation of an Antigravity conversation session exporter for LRH. It generalizes `ConversationExportManifest` for multi-source tools, verifies real JSONL transcript payloads, and bridges Antigravity session trajectories stored on disk with LRH's standardized conversation export manifest contract and sensitivity scanning pipeline.

## Scope

### Included
- `ConversationExportManifest` generalization for multi-source tools (`source_tool: antigravity`).
- Real-session JSONL payload dogfood verification.
- `src/lrh/conversations/antigravity_export.py` core export API using primary `--transcript-path` input.
- `tests/conversations_tests/antigravity_export_test.py` hermetic unit tests.
- `lrh conversation export-antigravity-session` CLI subcommand in `src/lrh/cli/main.py`.
- `src/lrh/skills/lrh-antigravity-export/SKILL.md` agent skill package.

### Excluded
- Custom desktop GUI chat panels.
- Automatic completion of work items from raw transcript text.

## Prior Art Check

### Duplication search
- In-repo: `pdf_import.py` (ChatGPT PDF) and `codex_file_export.py` (Codex text file). No existing Antigravity exporter.
- Sibling repos: None identified.
- External libraries: Google Antigravity SDK (`google-antigravity`).
- Recommendation: Proceed with workstream execution.

### Demand search
- Work items: None prior.
- Proposals: `PROP-LRH-ANTIGRAVITY-CONVERSATION-EXPORTER`.
- Recommendation: Proceed; link work items to this workstream.

## Work Items

- `WI-ANTIGRAVITY-CONVERSATION-EXPORT-API`: Implement Antigravity session export Python API.
- `WI-ANTIGRAVITY-CONVERSATION-EXPORT-CLI`: Implement `lrh conversation export-antigravity-session` CLI subcommand.
- `WI-ANTIGRAVITY-CONVERSATION-EXPORT-SKILL`: Implement native Antigravity export skill package.

## Exit Criteria

- `ConversationExportManifest` and `export_inspector.py` support `source_tool: antigravity`.
- Dogfood check confirms actual JSONL payload schemas from Antigravity `transcriptPath`.
- Python API in `src/lrh/conversations/antigravity_export.py` converts `transcriptPath` files into Markdown artifacts with valid `ConversationExportManifest` frontmatter and passes unit tests.
- CLI subcommand `lrh conversation export-antigravity-session` accepts `--transcript-path` and is available and tested.
- Native Antigravity skill package is created and passes `lrh validate`.

## Non-Goals

- Do not alter raw Antigravity log files on disk.
- Do not store raw transcript text in public repository state by default.
- Do not print raw transcript body to terminal output by default.
