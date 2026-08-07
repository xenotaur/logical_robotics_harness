---
id: WI-ANTIGRAVITY-CONVERSATION-EXPORT-API
title: Implement Antigravity session export Python API
type: deliverable
status: proposed
blocked: false
blocked_reason: null
resolution: null
related_workstreams:
  - WS-ANTIGRAVITY-CONVERSATION-EXPORT
depends_on: []
blocked_by: []
artifacts_expected:
  - src/lrh/conversations/export_manifest.py
  - src/lrh/conversations/export_inspector.py
  - src/lrh/conversations/antigravity_export.py
  - tests/conversations_tests/antigravity_export_test.py
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - ConversationExportManifest is generalized to support source_tool: antigravity and passes export_inspector validation.
  - Real-session JSONL payload dogfood check confirms step event schemas from transcriptPath.
  - Function convert_antigravity_session exists in src/lrh/conversations/antigravity_export.py accepting explicit transcript_path input.
  - Populates source_sha256, source_id, exported_at, transcript_statistics, sensitivity_scan, and warning attributes.
  - Fast hermetic unit tests pass in pytest with zero network access or raw transcript commits.
---

# WI-ANTIGRAVITY-CONVERSATION-EXPORT-API: Implement Antigravity session export Python API

## Summary

Implement Tranche 1 of the Antigravity conversation session exporter: generalize `ConversationExportManifest` for multi-source tools (`source_tool: antigravity`), run a dogfood check on real `transcriptPath` JSONL logs, and implement `src/lrh/conversations/antigravity_export.py` to parse session steps, run sensitivity scanning, build manifests, and render private Markdown export artifacts.

## Problem / Context

Antigravity stores session trajectories locally under `<appDataDir>/brain/<conversation-id>/.system_generated/logs/transcript.jsonl` (exposed via hook metadata as `transcriptPath`). Currently, LRH's `ConversationExportManifest` hardcodes `source_tool == "codex"`, which must be generalized before Antigravity session exports can be inspected and validated.

### Prior Art Check
- Duplication search: None found in `src/lrh/conversations/`.
- Demand search: Fulfills Tranche 1 of `PROP-LRH-ANTIGRAVITY-CONVERSATION-EXPORTER` and `WS-ANTIGRAVITY-CONVERSATION-EXPORT`.

## Scope

### Included
- Prerequisite generalization of `ConversationExportManifest` and `export_inspector.py` to support `source_tool: antigravity`.
- Dogfood check against real session `transcriptPath` JSONL files.
- `src/lrh/conversations/antigravity_export.py` module.
- `AntigravityExport` dataclass definition.
- `convert_antigravity_session` function with explicit `transcript_path` input support.
- `tests/conversations_tests/antigravity_export_test.py` unit tests.

### Excluded
- CLI argument parsing (handled in Tranche 2).
- Agent skill Markdown file (handled in Tranche 3).

## Required Changes

- Update `ConversationExportManifest` in `src/lrh/conversations/export_manifest.py` and `export_inspector.py` to accept `source_tool: antigravity` and generalize manifest validation.
- Create `src/lrh/conversations/antigravity_export.py`.
- Define `AntigravityExport` frozen dataclass with `markdown`, `manifest`, and `sensitivity_result`.
- Implement `convert_antigravity_session(transcript_path, *, output_path, force=False, ...)` returning `AntigravityExport`.
- Implement JSONL parsing logic to extract user messages, assistant responses, and tool calls.
- Add unit tests in `tests/conversations_tests/antigravity_export_test.py` testing valid parsing, malformed trailing lines, sensitivity scan warnings, manifest statistics, and output file collisions.

## Non-Goals

- Do not modify source `transcript.jsonl` files.
- Do not commit raw transcript payloads to public repo state.
- Do not make HTTP/network calls in unit tests.

## Acceptance Criteria

- `ConversationExportManifest` validates `source_tool: antigravity` exports cleanly under `export_inspector.py`.
- `src/lrh/conversations/antigravity_export.py` exists and exports `convert_antigravity_session`.
- Generates valid `ConversationExportManifest` frontmatter (`source_tool: antigravity`, `source_adapter: antigravity_transcript_jsonl`, `source_sha256`, `source_id`, `transcript_statistics`).
- Unit tests in `tests/conversations_tests/antigravity_export_test.py` pass cleanly.
- `lrh validate` reports 0 errors.

## Validation

- `pytest tests/conversations_tests/`
- `lrh validate`
