---
id: WI-ANTIGRAVITY-CONVERSATION-EXPORT-CLI
title: Implement lrh conversation export-antigravity-session CLI subcommand
type: deliverable
status: proposed
blocked: false
blocked_reason: null
resolution: null
related_workstreams:
  - WS-ANTIGRAVITY-CONVERSATION-EXPORT
depends_on:
  - WI-ANTIGRAVITY-CONVERSATION-EXPORT-API
blocked_by: []
artifacts_expected:
  - src/lrh/cli/main.py
  - src/lrh/conversations/antigravity_export.py
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - CLI subcommand lrh conversation export-antigravity-session is registered in src/lrh/cli/main.py.
  - Supports --conversation-id, --latest, --app-data-dir, --out, --force, and --no-scan-sensitive flags.
  - Outputs metadata-only terminal status without dumping raw transcript body.
  - Passes lrh validate and CLI parser tests.
---

# WI-ANTIGRAVITY-CONVERSATION-EXPORT-CLI: Implement lrh conversation export-antigravity-session CLI subcommand

## Summary

Implement Tranche 2 of the Antigravity conversation session exporter: register the `export-antigravity-session` subcommand under `lrh conversation` in `src/lrh/cli/main.py`, backed by the `src/lrh/conversations/antigravity_export.py` API.

## Problem / Context

Users and scripts need a CLI entry point to export local Antigravity sessions into Markdown artifacts without writing custom Python scripts.

### Prior Art Check
- Duplication search: `convert-codex-file` and `convert-pdf` subcommands exist in `src/lrh/cli/main.py`.
- Demand search: Fulfills Tranche 2 of `PROP-LRH-ANTIGRAVITY-CONVERSATION-EXPORTER` and `WS-ANTIGRAVITY-CONVERSATION-EXPORT`.

## Scope

### Included
- `run_convert_antigravity_session_cli` function in `src/lrh/conversations/antigravity_export.py`.
- Subcommand registration in `src/lrh/cli/main.py`.
- CLI unit tests in `tests/conversations_tests/antigravity_export_test.py`.

### Excluded
- Antigravity agent skill manifest (Tranche 3).

## Required Changes

- Implement `run_convert_antigravity_session_cli(argv, *, prog)` in `src/lrh/conversations/antigravity_export.py`.
- Register `export-antigravity-session` under `conversation` subparsers in `src/lrh/cli/main.py`.
- Wire flags: `--conversation-id`, `--latest`, `--app-data-dir`, `--out`, `--force`, `--no-scan-sensitive`.
- Print metadata summary (privacy, sensitivity status, warning count) to stderr/stdout on completion.

## Non-Goals

- Do not print raw transcript text to terminal output by default.

## Acceptance Criteria

- `lrh conversation export-antigravity-session --help` displays help documentation.
- `lrh conversation export-antigravity-session` correctly converts a session log into a Markdown export artifact.
- `lrh validate` reports 0 errors.

## Validation

- `lrh conversation export-antigravity-session --help`
- `pytest tests/conversations_tests/antigravity_export_test.py`
- `lrh validate`
