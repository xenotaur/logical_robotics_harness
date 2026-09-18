---
execution_id: 2026_09_18_01_33_14_ARCHIVE_ROOT_UNRESOLVABLE_HOME_CONFIRM
prompt_id: PROMPT(AD_HOC:ARCHIVE_ROOT_UNRESOLVABLE_HOME_CONFIRM)[2026-09-18T01:32:47+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/668
commit: 53f5257e1cf68b4d698ef686b6fc38166717c5ff
created_at: 2026-09-18T01:33:14+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/668
session_transcript: claude-app:96d435c4-74bf-4d21-a856-c74e60df120c
---

# Summary

Pre-merge verification pass for PR #668 (`fix(session-archive): catch
unresolvable-home RuntimeError in resolve_archive_root`), run via
`/lrh-land`'s inlined Step 5. No primary execution record exists for
this PR (opened ad hoc, not via `/lrh-implement`) -- `rerun_of` is left
empty per the found-or-backfill matrix; this run is itself part of the
backfill path `/lrh-land` Step 1 identified.

# Result

`lrh github threads --mode raw --state all` filtered to
`isResolved == false` returned 3 threads, all from automated reviewers
(copilot-pull-request-reviewer, chatgpt-codex-connector x2) on the
first-round push. Fresh-eyes verification against the current `HEAD`
diff (commit 3f8c1f25, pushed as a follow-up fix before this record was
created) classified all 3 as Clear-satisfied:

1. Copilot -- Codex archive/import CLI handlers (`run_archive_codex_thread_cli`,
   `run_import_codex_exports_cli`) caught only `(OSError, CodexArchiveError, ...)`
   around calls that resolve the archive root -- both now also catch
   `prompt_workflow_sessions.ArchiveRootResolutionError`.
2. chatgpt-codex-connector -- same underlying gap, additionally naming
   `lrh sessions sync` and `lrh memory sync`, which had no exception
   boundary at all around their archive-root-resolving calls -- both
   `_run_sync` functions now catch `ArchiveRootResolutionError`.
3. chatgpt-codex-connector -- `default_archive_root()`'s own
   `Path.home()` call was outside the `_expand_user_path()` wrapper, so
   the no-override/no-env-var default path still raised an unhandled
   `RuntimeError` -- now wrapped, raising the same
   `ArchiveRootResolutionError`.

`confirm_fixes_batch: auto_unless_unusual` autopilot check
(`lrh confirm-fixes check-batch-routine --bucket Clear-satisfied
--bucket Clear-satisfied --bucket Clear-satisfied`) reported "routine:
all 3 thread(s) are Clear-satisfied" (CI was provisionally pending, not
failing; no prior `_CONFIRM` exception on this PR) -- summary was still
presented per the gate's transparency requirement, and the live wait
was skipped per the autopilot result. All 3 threads resolved via
`resolveReviewThread`. Thread-resolution verdict: green.

# Validation

- `lrh github threads <pr-url> --mode raw --state all` -- 3 unresolved
  threads found, all Clear-satisfied against `HEAD` 3f8c1f25
- `gh pr checks <pr-url> --required` -- errored `no required checks
  reported`; distinguished via `gh api rules/branches/main` (0
  `required_status_checks` rules -> confirmed no required-check branch
  protection, not a timing race)
- `gh pr checks <pr-url>` (unfiltered, provisional) -- 3/5 `SUCCESS`
  (`lint`, `installed-wheel-smoke`, `Check workflow files`), 2/5
  `IN_PROGRESS` (`coverage`, `tests`) -- re-checked at Step 8 against
  this record's own post-push `HEAD`
- `lrh validate` -- run after this record is finalized, before push

# Follow-up

None -- proceeding to Step 8 (readiness report / REVIEW-LANDED
re-check against this record's own commit) once pushed.
