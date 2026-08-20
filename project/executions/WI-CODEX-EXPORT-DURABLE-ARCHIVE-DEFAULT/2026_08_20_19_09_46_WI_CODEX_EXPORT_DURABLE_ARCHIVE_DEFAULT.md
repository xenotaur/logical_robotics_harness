---
execution_id: 2026_08_20_19_09_46_WI_CODEX_EXPORT_DURABLE_ARCHIVE_DEFAULT
prompt_id: PROMPT(WI-CODEX-EXPORT-DURABLE-ARCHIVE-DEFAULT:WI_CODEX_EXPORT_DURABLE_ARCHIVE_DEFAULT)[2026-08-20T01:04:01+00:00]
work_item: WI-CODEX-EXPORT-DURABLE-ARCHIVE-DEFAULT
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/579
commit: 
created_at: 2026-08-20T19:09:46+00:00
agent: codex_app
instruction_source: project/work_items/proposed/WI-CODEX-EXPORT-DURABLE-ARCHIVE-DEFAULT.md
session_transcript: codex-app:019fc43f-e2d9-7503-88cb-9d9a8136c111
---

# Summary

Implement `WI-CODEX-EXPORT-DURABLE-ARCHIVE-DEFAULT`: make Codex exports
durable-archive-first, keep scratch mode explicit, add attempt/failure
metadata, import rescued Codex export directories, and update docs/tests/skill
mirrors.

# Result

- Added `lrh.conversations.codex_archive`, including durable archive-root
  resolution, date-bucketed Codex export/import paths, per-attempt
  `attempt.json`, explicit scratch mode, metadata-only CLI output, and import
  classification for valid, partial, empty, and invalid rescued export
  directories.
- Added `lrh conversation archive-codex-thread` and
  `lrh conversation import-codex-exports` CLI entry points.
- Updated `/lrh-codex-export` canonical and local mirrored skills so routine
  captures use the durable archive and temp directories are reserved for
  explicit `--scratch` dogfood/debug mode.
- Updated conversation docs and CLI reference with durable archive defaults,
  scratch mode, migration/import workflow, and privacy boundaries.
- Recorded the Codex archive-root decision in `WS-SESSION-ARCHIVE-SYNC`.
- Ran diff-mode self-review before opening the PR. The verified P1 finding
  found same-second export directory collisions could overwrite a previous
  `attempt.json`; fixed by reserving a unique durable directory before writing
  attempt metadata and added a regression test.

# Validation

- `scripts/version tools` — Python 3.11.8, Ruff 0.15.12, Black 26.3.1,
  Pylint 2.16.2.
- `scripts/format --check --diff` — 203 files would be left unchanged.
- `scripts/lint` — Ruff passed; Black check passed.
- `scripts/test` — 1114 tests OK.
- `lrh validate` — 0 errors, 0 warnings.
- `lrh skills check --target claude --local` — all skills up to date.
- `lrh skills check --target antigravity --local` — all skills and plugin
  manifest up to date.
- `lrh skills status --target codex --local` — all skills up to date, with
  expected `argument-hint` stripping notices.
- `lrh conversation archive-codex-thread --help` — command help renders.
- `lrh conversation import-codex-exports --help` — command help renders.
- `python -m unittest tests.conversations_tests.codex_archive_test
  tests.cli_tests.conversation_test` — 21 focused tests OK.

# Follow-up

- `lrh skills check --target codex --local` exits nonzero because it labels
  repository-wide expected `argument-hint` stripping as errors even though
  `lrh skills status --target codex --local` reports the same behavior as
  notices. This appears to be pre-existing installer/check semantics debt, not
  caused by this WI.
