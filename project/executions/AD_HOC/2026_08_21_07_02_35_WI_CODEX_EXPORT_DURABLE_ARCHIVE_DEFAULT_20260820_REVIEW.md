---
execution_id: 2026_08_21_07_02_35_WI_CODEX_EXPORT_DURABLE_ARCHIVE_DEFAULT_20260820_REVIEW
prompt_id: PROMPT(AD_HOC:WI_CODEX_EXPORT_DURABLE_ARCHIVE_DEFAULT_20260820_REVIEW)[2026-08-21T07:01:48+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_08_21_06_46_11_WI_CODEX_EXPORT_DURABLE_ARCHIVE_DEFAULT_20260820_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/579
commit: e094d443d813eabc81e96f95301fdc15ac5787ce
created_at: 2026-08-21T07:02:35+00:00
agent: codex_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/579
session_transcript: codex-app:019fc43f-e2d9-7503-88cb-9d9a8136c111
---

# Summary

Address a low-severity stale documentation finding from PR-mode substitute
self-review for PR #579.

# Result

- PR-mode substitute self-review found that
  `docs/conversations/conversation-capture-options.md` still described
  `/lrh-codex-export` as wrapping the low-level explicit-path
  `lrh conversation export-codex-thread`.
- Direct re-verification confirmed the finding at the capability table and
  private-export guidance sections before editing.
- Updated the capability table to recommend
  `lrh conversation archive-codex-thread --thread-id THREAD_ID` for the durable
  archive default and keep `export-codex-thread` only as the explicit
  `--out` / `--raw-out` path.
- Updated the prose guidance so `/lrh-codex-export` wraps
  `archive-codex-thread`, writes into the durable private session archive,
  inspects the export, and reports metadata only.

# Validation

- `env PATH=/Users/centaur/anaconda3/bin:$PATH scripts/version tools` —
  Python 3.11.8, Ruff 0.15.12, Black 26.3.1, Pylint 2.16.2.
- `sed -n '32,76p' docs/conversations/conversation-capture-options.md` —
  stale references replaced with durable archive guidance.
- `rg -n 'archive-codex-thread|export-codex-thread|lrh-codex-export' docs/conversations/conversation-capture-options.md`
  — durable wrapper and explicit-path distinction visible.
- `env PATH=/Users/centaur/anaconda3/bin:$PATH scripts/format --check --diff`
  — 203 files would be left unchanged.
- `env PATH=/Users/centaur/anaconda3/bin:$PATH scripts/lint` — Ruff passed;
  Black check passed.
- `env PYTHONNOUSERSITE=1 PYTHONPATH=... PATH=/Users/centaur/anaconda3/bin:$PATH lrh validate`
  — 0 errors, 0 warnings.
- Full `scripts/test` was not rerun for this docs-only follow-up; the earlier
  code review-response round passed 1115 tests.

# Follow-up

- Rerun confirm-fixes from the top against the new PR head.
