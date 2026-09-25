---
execution_id: 2026_09_22_06_30_10_ARCHIVE_ROOT_UNRESOLVABLE_HOME_REVIEW
prompt_id: PROMPT(AD_HOC:ARCHIVE_ROOT_UNRESOLVABLE_HOME_REVIEW)[2026-09-22T06:30:04+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/668
commit: 53f5257e1cf68b4d698ef686b6fc38166717c5ff
created_at: 2026-09-22T06:30:10+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/668
session_transcript: claude-app:96d435c4-74bf-4d21-a856-c74e60df120c
---

# Summary

Backfilled record for PR #668's review-response round, authored
retroactively (session interrupted before this record was created; PR
is already merged and closed out). Documents the round-1 automated
review fix that ran before `/lrh-confirm-fixes` -- captured here for
audit-trail completeness, not as a live review-fix session. No primary
execution record ever existed for this PR (opened ad hoc, not via
`/lrh-implement`) -- `rerun_of` is left empty per the found-or-backfill
matrix, consistent with the `_CONFIRM`/`_SELFREVIEW`/`_CLOSEOUT`
backfill records already on this PR.

# Result

First-round automated review (Copilot `copilot-pull-request-reviewer`,
`chatgpt-codex-connector`) on the initial fix commit (`5d13b459`) found
it incomplete: it wrapped `.expanduser()`/`.home()` calls only inside
`claude_export.py` and `antigravity_export.py`, leaving three related
gaps --

1. `codex_archive.py`'s `run_archive_codex_thread_cli()` and
   `run_import_codex_exports_cli()` caught only
   `(OSError, CodexArchiveError, ...)` around calls that resolve the
   archive root via the shared resolver.
2. `sessions_workflow.py`'s `_run_sync()` (`lrh sessions sync`) and
   `memory_workflow.py`'s `_run_sync()` (`lrh memory sync`) had no
   exception boundary at all around their
   `resolve_archive_root()`/`sync_memory()` calls.
3. `default_archive_root()`'s own `Path.home()` call, in
   `prompt_workflow_sessions.py`, was outside the `_expand_user_path()`
   wrapper, so the no-override/no-env-var default path still raised an
   unhandled `RuntimeError`.

Fixed in commit `3f8c1f25`: added `ArchiveRootResolutionError` catches
at every remaining CLI boundary that resolves an archive root, and
wrapped `default_archive_root()`'s `Path.home()` call the same way the
override/env-var paths already were. Added regression tests for each
newly-guarded entry point and the unresolvable-default-home case.
Pushed directly to the open PR branch.

# Validation

- `scripts/format --check --diff` -- clean
- `scripts/lint` -- clean (ruff + black + test-framework guardrails)
- `PYTHONPATH=src python3 -m pytest tests/` -- 1601 passed (non-canonical
  raw pytest invocation used at the time instead of `scripts/test`; noted
  here for accuracy since this is a backfilled historical record, not a
  recommendation to repeat)

# Follow-up

None -- superseded by the `_CONFIRM` record's fresh-eyes verification,
which resolved all 3 review threads and reached a Green merge-readiness
verdict.
