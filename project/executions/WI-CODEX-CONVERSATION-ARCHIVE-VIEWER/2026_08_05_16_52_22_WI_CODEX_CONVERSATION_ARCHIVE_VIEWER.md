---
execution_id: 2026_08_05_16_52_22_WI_CODEX_CONVERSATION_ARCHIVE_VIEWER
prompt_id: PROMPT(WI-CODEX-CONVERSATION-ARCHIVE-VIEWER:WI_CODEX_CONVERSATION_ARCHIVE_VIEWER)[2026-08-05T06:31:35+00:00]
work_item: WI-CODEX-CONVERSATION-ARCHIVE-VIEWER
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/492
commit: 59ae473d3c2b4c7e9eb5937cd071bf7d0d4e9d91
agent: codex_app
instruction_source: skill:lrh-execute WI-CODEX-CONVERSATION-ARCHIVE-VIEWER
session_transcript: none
created_at: 2026-08-05T16:52:22+00:00
---

# Summary

Implemented the safe-default Codex conversation archive viewer for explicitly
configured local Markdown export roots in `lrh serve`.

# Result

- Added repeatable `--codex-archive-root PATH` configuration.
- Added read-only HTML routes for archive index and export detail pages.
- Added metadata-only API routes for archive index and export detail payloads.
- Reused the Codex export inspector for manifest/statistics metadata.
- Rendered transcript body text only on explicit valid-export HTML detail
  routes, escaped as inert text.
- Kept invalid exports metadata-only and blocked detail-body rendering.
- Updated CLI and conversation-capture documentation.
- Opened PR #492: https://github.com/xenotaur/logical_robotics_harness/pull/492

# Validation

- `scripts/version tools`
- `scripts/lint`
- `PYTHONPATH=src python -m unittest tests.cli_tests.serve_test` (unsandboxed
  for loopback socket binding): 63 tests OK.
- `PYTHONPATH=src scripts/test` (unsandboxed for loopback socket binding): 958
  tests OK plus scripted smoke checks.
- `PYTHONPATH=src python -m lrh.cli.main validate`: 0 errors, 0 warnings.
- Fresh independent self-review found invalid-export rendering and path-leak
  risks; both were fixed and the reviewer re-checked the updated diff as clean.

# Follow-up

- Consider pagination or caching if archive roots become large enough for
  recursive per-request scans to be slow.
