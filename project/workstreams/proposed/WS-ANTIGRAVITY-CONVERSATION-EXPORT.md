---
id: WS-ANTIGRAVITY-CONVERSATION-EXPORT
kind: planning_node
title: Antigravity Conversation Session Exporter
status: proposed
stage: planned
summary: "Orchestrates the 3-tranche implementation of the Antigravity conversation session exporter, spanning Python API library code, lrh conversation CLI integration, and a native Antigravity skill package."
related_design:
  - project/design/proposals/proposed/lrh-antigravity-conversation-exporter/00_proposal.md
  - project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md
work_items:
  - WI-ANTIGRAVITY-CONVERSATION-EXPORT-API
  - WI-ANTIGRAVITY-CONVERSATION-EXPORT-CLI
  - WI-ANTIGRAVITY-CONVERSATION-EXPORT-SKILL
exit_criteria:
  - Python API in src/lrh/conversations/antigravity_export.py parses Antigravity JSONL logs into Markdown artifacts with valid ConversationExportManifest frontmatter and passes hermetic unit tests.
  - CLI subcommand lrh conversation export-antigravity-session is registered in src/lrh/cli/main.py and passes CLI integration tests.
  - Native Antigravity skill in src/lrh/skills/lrh-antigravity-export/ passes skill check and lrh validate cleanly.
---

# Antigravity Conversation Session Exporter Workstream

## Purpose

This workstream coordinates the 3-tranche implementation of an Antigravity conversation session exporter for LRH. It bridges Antigravity session trajectories stored on disk with LRH's standardized conversation export manifest contract and sensitivity scanning pipeline.

## Scope

### Included
- `src/lrh/conversations/antigravity_export.py` core export API.
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

- Python API in `src/lrh/conversations/antigravity_export.py` converts `transcript.jsonl` files into Markdown artifacts with valid `ConversationExportManifest` frontmatter and passes unit tests.
- CLI subcommand `lrh conversation export-antigravity-session` is available and tested.
- Native Antigravity skill package is created and passes `lrh validate`.

## Non-Goals

- Do not alter raw Antigravity log files on disk.
- Do not store raw transcript text in public repository state by default.
