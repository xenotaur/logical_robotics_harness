---
execution_id: 2026_08_21_05_33_22_WI_CODEX_EXPORT_DURABLE_ARCHIVE_DEFAULT_20260820_REVIEW
prompt_id: PROMPT(AD_HOC:WI_CODEX_EXPORT_DURABLE_ARCHIVE_DEFAULT_20260820_REVIEW)[2026-08-21T05:27:22+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_08_20_19_09_46_WI_CODEX_EXPORT_DURABLE_ARCHIVE_DEFAULT
pr: https://github.com/xenotaur/logical_robotics_harness/pull/579
commit: 
created_at: 2026-08-21T05:33:22+00:00
agent: codex_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/579
session_transcript: codex-app:019fc43f-e2d9-7503-88cb-9d9a8136c111
---

# Summary

Address PR #579 review findings against the Codex durable archive default
implementation.

# Result

- Fixed imported `export.md` permissions by chmod'ing copied Markdown
  transcripts to private mode (`0600`) just like `raw.json` and
  `attempt.json`.
- Fixed the P1 worktree-safety gap by rejecting durable archive roots that
  resolve inside the current Git worktree before export/import destinations
  are used.
- Fixed timestamp provenance drift by resolving the archive export timestamp
  once and passing that same value to the low-level Codex app-server exporter,
  so the archive date bucket and manifest `exported_at` agree even around UTC
  boundaries.
- Updated Codex export docs and CLI reference to state the active worktree
  rejection and imported-file private-mode behavior.

# Validation

- `env PATH=/Users/centaur/anaconda3/bin:$PATH scripts/version tools` —
  Python 3.11.8, Ruff 0.15.12, Black 26.3.1, Pylint 2.16.2.
- `env PATH=/Users/centaur/anaconda3/bin:$PATH scripts/format --check --diff`
  — 203 files would be left unchanged.
- `env PATH=/Users/centaur/anaconda3/bin:$PATH scripts/lint` — Ruff passed;
  Black check passed.
- `env PYTHONNOUSERSITE=1 PYTHONPATH=... PATH=/Users/centaur/anaconda3/bin:$PATH python -m unittest tests.conversations_tests.codex_archive_test`
  — 9 tests OK.
- `env PYTHONNOUSERSITE=1 PYTHONPATH=... PATH=/Users/centaur/anaconda3/bin:$PATH scripts/test`
  — 1115 tests OK after rerunning with sandbox escalation for localhost serve
  tests; the first sandboxed attempt failed only with `PermissionError` on
  socket bind in `cli_tests.serve_test`.
- `env PYTHONNOUSERSITE=1 PYTHONPATH=... PATH=/Users/centaur/anaconda3/bin:$PATH lrh validate`
  — 0 errors, 0 warnings.

# Follow-up

- None for this review-response round.
