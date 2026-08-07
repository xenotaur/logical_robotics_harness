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
  - src/lrh/conversations/antigravity_export.py
  - tests/conversations_tests/antigravity_export_test.py
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - Function convert_antigravity_session exists in src/lrh/conversations/antigravity_export.py.
  - Parses transcript.jsonl lines into user, assistant, and tool call Markdown sections.
  - Integrates with lrh.conversations.sensitivity and builds ConversationExportManifest.
  - Fast hermetic unit tests pass in pytest.
---

# WI-ANTIGRAVITY-CONVERSATION-EXPORT-API: Implement Antigravity session export Python API

## Summary

Implement Tranche 1 of the Antigravity conversation session exporter: a typed Python library module `src/lrh/conversations/antigravity_export.py` that reads Antigravity `transcript.jsonl` log files, parses conversation step objects, runs sensitivity scanning, builds frontmatter manifests, and renders private Markdown export artifacts.

## Problem / Context

Antigravity stores session trajectories locally under `<appDataDir>/brain/<conversation-id>/.system_generated/logs/transcript.jsonl`. Currently, LRH does not have an API module to parse these session logs into standardized `ConversationExportManifest` Markdown artifacts.

### Prior Art Check
- Duplication search: None found in `src/lrh/conversations/`.
- Demand search: Fulfills Tranche 1 of `PROP-LRH-ANTIGRAVITY-CONVERSATION-EXPORTER` and `WS-ANTIGRAVITY-CONVERSATION-EXPORT`.

## Scope

### Included
- `src/lrh/conversations/antigravity_export.py` module.
- `AntigravityExport` dataclass definition.
- `convert_antigravity_session` function supporting file path or conversation ID input.
- `tests/conversations_tests/antigravity_export_test.py` unit tests.

### Excluded
- CLI argument parsing (handled in Tranche 2).
- Agent skill Markdown file (handled in Tranche 3).

## Required Changes

- Create `src/lrh/conversations/antigravity_export.py`.
- Define `AntigravityExport` frozen dataclass with `markdown`, `manifest`, and `sensitivity_result`.
- Implement `convert_antigravity_session(source_path, *, output_path, force=False, ...)` returning `AntigravityExport`.
- Implement JSONL parsing logic to extract `USER_INPUT`, `PLANNER_RESPONSE`, `MODEL`, and `tool_calls`.
- Add unit tests in `tests/conversations_tests/antigravity_export_test.py` testing valid parsing, malformed trailing lines, sensitivity scan warnings, and output file collisions.

## Non-Goals

- Do not modify source `transcript.jsonl` files.
- Do not make HTTP/network calls in unit tests.

## Acceptance Criteria

- `src/lrh/conversations/antigravity_export.py` exists and exports `convert_antigravity_session`.
- Generates valid `ConversationExportManifest` frontmatter (`source_tool: antigravity`, `source_adapter: antigravity_transcript_jsonl`).
- Unit tests in `tests/conversations_tests/antigravity_export_test.py` pass cleanly.
- `lrh validate` reports 0 errors.

## Validation

- `pytest tests/conversations_tests/antigravity_export_test.py`
- `lrh validate`
