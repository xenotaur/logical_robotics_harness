---
execution_id: 2026_08_04_19_59_16_WI_CODEX_CONVERSATION_INSPECT_EXPORT
prompt_id: PROMPT(WI-CODEX-CONVERSATION-INSPECT-EXPORT:WI_CODEX_CONVERSATION_INSPECT_EXPORT)[2026-08-04T19:44:28+00:00]
work_item: WI-CODEX-CONVERSATION-INSPECT-EXPORT
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/484
commit:
created_at: 2026-08-04T19:59:16+00:00
agent: codex_app
instruction_source: project/work_items/proposed/WI-CODEX-CONVERSATION-INSPECT-EXPORT.md
session_transcript: none
---

# Summary

Implement the Codex conversation export inspector CLI.

# Result

Added `lrh conversation inspect-export EXPORT.md --format text|json
[--source SOURCE]` backed by `lrh.conversations.export_inspector`.

The inspector validates `ConversationExportManifest` frontmatter, reports
privacy/authority/sensitivity/warning metadata, recomputes artifact body
statistics, optionally verifies an explicit source SHA-256 hash, and keeps
default text and JSON output metadata-only so transcript body, snippets, and
message text are not echoed to terminal output or CI logs.

Fresh diff-mode self-review found one body-statistic drift edge case in the
initial implementation. The fix tightened renderer-added trailing-newline
normalization and added a regression test for extra trailing-newline drift.

# Validation

- `scripts/version tools` — Black 26.3.1, Ruff 0.15.12, Python 3.11.8.
- `scripts/format --check --diff` — 189 files unchanged.
- `scripts/lint` — all checks passed.
- `PYTHONPATH=src python -m unittest tests.conversations_tests.export_inspector_test tests.cli_tests.conversation_test` — 23 tests OK.
- `PYTHONPATH=src scripts/test` — 947 tests OK; release smoke passed.
- `PYTHONPATH=src python -m lrh.cli.main validate` — 0 errors, 0 warnings.

# Follow-up

Land PR #484 through `/lrh-land`, then close out
`WI-CODEX-CONVERSATION-INSPECT-EXPORT`.
