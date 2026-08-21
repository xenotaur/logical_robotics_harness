---
execution_id: 2026_08_21_18_12_36_WI_SESSION_SYNC_NESTED_ARTIFACTS
prompt_id: PROMPT(WI-SESSION-SYNC-NESTED-ARTIFACTS:WI_SESSION_SYNC_NESTED_ARTIFACTS)[2026-08-21T17:55:30+00:00]
work_item: WI-SESSION-SYNC-NESTED-ARTIFACTS
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/592
commit: 
created_at: 2026-08-21T18:12:36+00:00
agent: codex_app
instruction_source: project/work_items/proposed/WI-SESSION-SYNC-NESTED-ARTIFACTS.md
session_transcript: codex-app:019fc43f-e2d9-7503-88cb-9d9a8136c111
---

# Summary

Implement `WI-SESSION-SYNC-NESTED-ARTIFACTS`: extend `lrh sessions sync`
to mirror nested session-adjacent artifacts in addition to top-level
Claude Code JSONL transcripts.

# Result

- Added `DiscoveredTranscript`, carrying source path, owning archive slug,
  relative destination path, and top-level/nested classification.
- Updated transcript discovery to build a global top-level
  `session-id -> slug` map, redirect nested artifacts to the owning slug,
  preserve UUID-ish orphan session directories under their local slug, and
  exclude ordinary non-session directories such as `memory/`.
- Extended `mirror_transcript` with a safe relative destination path while
  preserving the existing atomic-write and never-shrink behavior.
- Updated `lrh sessions sync` so `--dry-run` reports the true destination
  path and child-id alias reconciliation runs only for top-level
  transcripts.
- Added focused helper and CLI coverage for top-level compatibility, nested
  mirroring, cross-bucket ownership, orphan fallback, non-session exclusion,
  unsafe relative paths, true dry-run output, and top-level-only alias
  reconciliation.

# Validation

- `env PATH=/Users/centaur/anaconda3/bin:$PATH scripts/version tools` —
  Python 3.11.8, Ruff 0.15.12, Black 26.3.1, Pylint 2.16.2.
- `env PATH=/Users/centaur/anaconda3/bin:$PATH scripts/format --check --diff`
  — 213 files unchanged.
- `env PATH=/Users/centaur/anaconda3/bin:$PATH scripts/lint` — Ruff and Black
  checks passed.
- `PYTHONPATH=src python -m unittest tests.assist_tests.prompt_workflow_sessions_test tests.cli_tests.sessions_test`
  — 62 tests OK.
- `env PYTHONNOUSERSITE=1 PYTHONPATH=/Users/centaur/.codex/worktrees/b1ba/logical_robotics_harness/src PATH=/Users/centaur/anaconda3/bin:$PATH scripts/test`
  — 1230 tests OK.
- `PYTHONPATH=src lrh validate` — 0 errors, 0 warnings.

# Follow-up

- Continue `WS-SESSION-ARCHIVE-SYNC` with later-stage `lrh sessions report`,
  closeout/scheduled sync wiring, and proposal adoption after this leaf lands.
