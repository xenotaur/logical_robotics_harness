---
execution_id: 2026_09_18_19_47_43_ARCHIVE_ROOT_UNRESOLVABLE_HOME_CLOSEOUT
prompt_id: PROMPT(AD_HOC:ARCHIVE_ROOT_UNRESOLVABLE_HOME_CLOSEOUT)[2026-09-18T19:47:38+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/668
commit: 53f5257e1cf68b4d698ef686b6fc38166717c5ff
created_at: 2026-09-18T19:47:43+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/668
session_transcript: claude-app:96d435c4-74bf-4d21-a856-c74e60df120c
---

# Summary

Backfill primary execution record for PR #668 (`fix(session-archive):
catch unresolvable-home RuntimeError in resolve_archive_root`),
authored by `/lrh-land` Step 7. PR #668 was opened ad hoc (implementing
a fix requested directly in chat, not via `/lrh-implement`), so no
primary implementation record was ever created for it; `/lrh-land`
Step 1's primary-record search found nothing, establishing the
backfill path. This record stands in as the primary for closeout
purposes and carries the run's CHAIN-NOTE.

# Result

`resolve_archive_root()` in `src/lrh/prompt_workflow_sessions.py`
called `Path.expanduser()`/`Path.home()` without catching the
`RuntimeError` raised when the home directory can't be resolved (e.g.
`HOME` unset, no passwd entry); CLI entry points that resolve an
archive root only caught `(*ExportError, OSError)`, so an
unresolvable-home value produced an unhandled traceback instead of a
clean nonzero-exit error. Fixed by adding `ArchiveRootResolutionError`
and wrapping every `.expanduser()`/`.home()` call in
`prompt_workflow_sessions.py`, then catching it at every CLI boundary
that resolves an archive root: `claude_export.py`,
`antigravity_export.py`, `codex_archive.py` (both CLI entry points),
`sessions_workflow.py` (`lrh sessions sync`), and `memory_workflow.py`
(`lrh memory sync`).

First-round automated review (Copilot, chatgpt-codex-connector) found
the initial fix incomplete -- it covered only the Claude/Antigravity
export CLIs, missing the Codex archive/import CLIs, `lrh sessions
sync`, `lrh memory sync`, and `default_archive_root()`'s own unwrapped
`Path.home()` call. A follow-up commit closed all four gaps. A
`/lrh-confirm-fixes` pass then verified the fix against the live diff,
resolved all 3 threads, and reached a Green verdict after CI passed
and a substitute `/lrh-self-review` PR-mode pass (no automatic bot
response had landed on the `_CONFIRM` commit after a reasonable wait)
came back clean. Merged via `gh pr merge --merge --match-head-commit`
at commit `53f5257e`.

CHAIN-NOTE: cycles=1; stops=0; gates=[merge]; friction=incomplete-first-fix; self_review_rounds=1; note="Initial fix covered only the two export CLIs' resolve calls; first-round review (Copilot + Codex) surfaced 3 related gaps (Codex CLIs, sessions/memory sync, default_archive_root's own Path.home()) requiring one follow-up commit before confirm-fixes went green. No automatic bot re-review landed on the _CONFIRM commit after ~10 minutes; substituted a clean /lrh-self-review PR-mode pass."

# Validation

- `PYTHONPATH=src python3 -m pytest tests/` -- 1601 passed
- `scripts/format --check --diff` -- clean
- `scripts/lint` -- clean (ruff + black + test-framework guardrails)
- `gh pr checks <pr-url>` -- 5/5 `SUCCESS` at merge time
- `lrh github threads <pr-url> --mode raw --state all` -- all 3 threads
  `isResolved: true`
- `lrh validate` -- 0 errors (1 pre-existing unrelated warning)

# Follow-up

None.
