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
  - Primary input route is --transcript-path PATH, with --conversation-id, --latest, --app-data-dir as optional discovery flags.
  - Outputs metadata-only terminal status without dumping raw transcript body.
  - Generated Markdown artifact passes lrh conversation inspect-export verification.
  - Passes lrh validate and CLI parser tests.
---

# WI-ANTIGRAVITY-CONVERSATION-EXPORT-CLI: Implement lrh conversation export-antigravity-session CLI subcommand

## Summary

Implement Tranche 2 of the Antigravity conversation session exporter: register the `export-antigravity-session` subcommand under `lrh conversation` in `src/lrh/cli/main.py`, backed by the `src/lrh/conversations/antigravity_export.py` API with `--transcript-path PATH` as the primary input route.

## Problem / Context

Antigravity hooks pass explicit `transcriptPath` metadata. Users and scripts need a CLI command `lrh conversation export-antigravity-session --transcript-path PATH --out EXPORT.md` to export sessions with metadata-only terminal reporting and full compatibility with `lrh conversation inspect-export`.

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
- Make `--transcript-path PATH` the primary required input option (or file path argument), while keeping `--conversation-id`, `--latest`, and `--app-data-dir` as optional discovery conveniences.
- Support `--out`, `--force`, `--no-scan-sensitive`.
- Print metadata-only summary (privacy, sensitivity status, warning count, hashes) to terminal output; never dump raw transcript body to stdout/stderr by default.

## Non-Goals

- Do not print raw transcript text to terminal output by default.

## Acceptance Criteria

- `lrh conversation export-antigravity-session --help` displays help documentation.
- `lrh conversation export-antigravity-session --transcript-path PATH --out EXPORT.md` converts session logs cleanly.
- Exported artifacts pass `lrh conversation inspect-export EXPORT.md`.
- `lrh validate` reports 0 errors.

## Validation

- `lrh conversation export-antigravity-session --help`
- `pytest tests/conversations_tests/antigravity_export_test.py`
- `lrh validate`
