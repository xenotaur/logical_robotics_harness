---
execution_id: 2026_07_30_21_38_31_SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS_REVIEW
prompt_id: PROMPT(AD_HOC:SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS_REVIEW)[2026-07-30T21:38:17+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_07_30_21_01_24_SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS
pr: https://github.com/xenotaur/logical_robotics_harness/pull/443
commit: 
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/443
session_transcript: claude-app:3fcab22f-9ebe-4392-bf31-2103fce507f2
created_at: 2026-07-30T21:38:31+00:00
---

# Summary

Round 1 review response for PR #443. Codex (chatgpt-codex-connector)
posted 3 P2 findings against HEAD `12c493e`.

# Result

- **Run remote discovery against the requested project root** (valid,
  fixed): `find_remote_matches`/`check_slug` ran `git`/`gh` in the
  process's own cwd regardless of `--project-root`. Added
  `_make_default_git_runner`/`_make_default_gh_runner` factories binding
  both to `project_root` via `cwd`; added an optional `cwd` parameter to
  `lrh.integrations.github.gh_client.run_gh_json`. Regression test added:
  `test_default_git_runner_binds_to_project_root_not_process_cwd`.
- **Stop when the latest match has an unresolved status** (valid, fixed):
  `SlugCheckResult.blocking` previously treated any non-`landed`/
  `in_progress` status (including `planned`, missing, or garbage values)
  as non-blocking, permitting a duplicate mint on an unresolved outcome.
  This was a real regression against the shell-based logic being
  replaced, which explicitly treated "unknown or ambiguous status" as a
  stop condition. Fixed: `blocking` now returns true for anything except
  the three explicit terminal statuses (`failed`/`reverted`/
  `superseded`); added `unresolved_status` to distinguish an ordinary
  blocking match from one that blocks only because its status couldn't be
  classified, for a clearer message. Updated all 5 migrated skills'
  SKILL.md (and 3 reference-doc) exit-code descriptions to match, since
  they had inherited the same incorrect "planned is non-blocking" framing.
  Tests added/fixed:
  `test_unrecognized_planned_status_blocks_as_unresolved`,
  `test_missing_or_garbage_status_blocks_as_unresolved`,
  `test_known_blocking_status_is_not_flagged_unresolved`.
- **Preserve filename matches whose records fail to parse** (valid,
  fixed): `find_local_matches` silently dropped a trailing-segment
  filename match when `parse_execution_record` returned `None` (malformed
  frontmatter), which could report "no prior record" for a match that
  genuinely exists but is unparseable. Fixed: preserved as a `SlugMatch`
  with `status="unparseable"`, which the `blocking`/`unresolved_status`
  fix above now correctly treats as blocking rather than absent. Test
  added: `test_unparseable_matching_file_is_preserved_not_dropped`.

# Validation

- `pytest tests/` — 825 passed (up from 821; +4 new/adjusted slug tests),
  same 1 pre-existing unrelated failure as before this PR
  (`version_integration_test.py`).
- `pytest tests/assist_tests/prompt_workflow_slug_test.py` — 17 passed.
- `scripts/format --check` / `scripts/lint` — clean.
- `lrh validate` — 0 errors, 1 pre-existing unrelated warning.
- Manual: `lrh prompt check-execution --slug idempotence-check-refinements
  --no-remote --project-root .` still correctly blocks on PR #441's landed
  record after the fix.

# Follow-up

None beyond what the primary record already tracks.
