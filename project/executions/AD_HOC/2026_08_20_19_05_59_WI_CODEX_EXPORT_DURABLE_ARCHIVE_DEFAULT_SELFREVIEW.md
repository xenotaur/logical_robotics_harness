---
execution_id: 2026_08_20_19_05_59_WI_CODEX_EXPORT_DURABLE_ARCHIVE_DEFAULT_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_CODEX_EXPORT_DURABLE_ARCHIVE_DEFAULT_SELFREVIEW)[2026-08-20T19:05:52+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-08-20T19:05:59+00:00
agent: codex_app
instruction_source: project/work_items/proposed/WI-CODEX-EXPORT-DURABLE-ARCHIVE-DEFAULT.md
session_transcript: codex-app:019fc43f-e2d9-7503-88cb-9d9a8136c111
---

# Summary

Diff-mode self-review for `WI-CODEX-EXPORT-DURABLE-ARCHIVE-DEFAULT`, run before
opening the implementation PR. The review covered the working-tree diff against
`origin/main`, including the new untracked `codex_archive` module and tests.

# Result

The cold-context reviewer reported three findings:

- P1: same-second durable exports for the same thread could reuse the same
  directory and overwrite a previous `attempt.json` with a later failed attempt.
- P2: the new implementation and test files were still untracked, meaning the PR
  would be incomplete if committed without `git add`.
- P3: the opening descriptions in the Codex export docs and skill still said
  `/lrh-codex-export` wrapped the lower-level `export-codex-thread` command.

The invoking session independently re-verified the P1 finding by reading
`src/lrh/conversations/codex_archive.py`: `plan_codex_export_paths()` built the
durable directory from second-level timestamp plus thread id, and
`archive_codex_thread()` wrote `attempt.json` before the lower-level exporter
rejected existing output files. The issue was fixed by reserving a unique
durable directory before writing `attempt.json`; same-second retries now use a
numbered suffix instead of touching the previous attempt directory.

P3 was fixed by updating the canonical skill and conversation guide to name
`archive-codex-thread` as the normal wrapper. P2 will be handled by staging the
new files before the implementation commit.

# Validation

- `python -m unittest tests.conversations_tests.codex_archive_test tests.cli_tests.conversation_test` — 21 tests OK.
- `scripts/format --check --diff` — 203 files would be left unchanged.
- `scripts/lint` — Ruff passed; Black check passed.
- `lrh validate` — 0 errors, 0 warnings.
- `git diff --check origin/main` — clean.

# Follow-up

- `lrh skills check --target codex --local` currently reports repository-wide
  `argument-hint` stripping as errors even though `lrh skills status --target
  codex --local` reports the same target-adapter behavior as notices. This is
  pre-existing installer/check semantics debt, not introduced by this change.
