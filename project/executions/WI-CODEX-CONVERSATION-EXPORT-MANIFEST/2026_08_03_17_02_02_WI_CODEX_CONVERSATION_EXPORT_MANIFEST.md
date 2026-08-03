---
execution_id: 2026_08_03_17_02_02_WI_CODEX_CONVERSATION_EXPORT_MANIFEST
prompt_id: PROMPT(WI-CODEX-CONVERSATION-EXPORT-MANIFEST:WI_CODEX_CONVERSATION_EXPORT_MANIFEST)[2026-08-03T16:45:59+00:00]
work_item: WI-CODEX-CONVERSATION-EXPORT-MANIFEST
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/476
commit:
agent: codex_app
instruction_source: project/work_items/proposed/WI-CODEX-CONVERSATION-EXPORT-MANIFEST.md
session_transcript: pending
created_at: 2026-08-03T17:02:02+00:00
---

# Summary

Implement `WI-CODEX-CONVERSATION-EXPORT-MANIFEST`.

# Result

Added a typed Codex conversation export manifest contract:

- `src/lrh/conversations/export_manifest.py` defines
  `ConversationExportManifest`, `TranscriptStatistics`, validation errors,
  Codex/private/non-authoritative defaults, deterministic mapping/frontmatter
  rendering, and `build_codex_manifest` / `statistics_for_text` helpers.
- `src/lrh/conversations/__init__.py` exports the public manifest helpers.
- `tests/conversations_tests/export_manifest_test.py` covers valid manifests,
  malformed required fields, default handling, non-Codex source-tool rejection,
  sensitivity metadata, warnings, transcript statistics, and stable serialized
  output.
- `docs/reference/cli/conversation.md` documents the manifest fields and states
  that raw Codex exports remain private, non-authoritative context.

The implementation intentionally does not include a Codex file adapter,
`inspect-export` CLI, viewer support, `session_transcript` grammar changes, or
raw transcript exports.

Prior-art check: present in the work item. Related prior art is the existing
ChatGPT PDF import path and sensitivity scanner; no duplicate Codex manifest
helper existed.

# Validation

- `scripts/version tools`: Black 26.3.1, Ruff 0.15.12, Python 3.11.8; Pyright not installed.
- `scripts/format --check --diff`: 184 files unchanged.
- `scripts/lint`: Ruff passed; Black reported 184 files unchanged.
- `PYTHONPATH=src python -m unittest tests.conversations_tests.export_manifest_test`: 11 tests OK.
- `PYTHONPATH=src scripts/test`: 885 tests OK outside the sandbox after the sandboxed run failed on loopback socket binding with `PermissionError: [Errno 1] Operation not permitted`.
- `PYTHONPATH=src python -m lrh.cli.main validate`: 0 errors, 0 warnings.

# Follow-up

Continue through `/lrh-land` for PR #476. Later work items should implement the
file-based Codex adapter, `inspect-export` CLI, and viewer follow-up.
