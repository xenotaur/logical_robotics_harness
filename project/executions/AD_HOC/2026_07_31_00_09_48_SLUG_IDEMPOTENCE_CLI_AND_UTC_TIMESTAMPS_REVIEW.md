---
execution_id: 2026_07_31_00_09_48_SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS_REVIEW
prompt_id: PROMPT(AD_HOC:SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS_REVIEW)[2026-07-31T00:08:57+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_07_30_23_42_03_SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/443
commit: fa8c573ec2af152ba7763134cb1207e040383393
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/443
session_transcript: claude-app:3fcab22f-9ebe-4392-bf31-2103fce507f2
created_at: 2026-07-31T00:09:48+00:00
---

# Summary

Round 6 review response for PR #443 — the last round auto-fixed per
explicit user direction ("keep auto-fixing for 2 more rounds if bugs
persist, then report back either way"). Codex reviewed at commit
`4f95850`. 2 new genuine findings, one of which is a real refinement of
round 2's own fix; remaining threads are stale duplicates of
already-fixed round-1 through round-5 issues awaiting
`/lrh-confirm-fixes`.

# Result

- **Codex: "Reject matches without a usable execution ID"** (valid,
  fixed): a match with a valid terminal `status`/`created_at` but a
  blank or missing `execution_id` (malformed frontmatter, or a field
  present with a non-string value) was silently reported with an empty
  `execution_id` — the migrated skills' guidance tells them to link
  `rerun_of` to that value, so a rerun would lose its lineage entirely
  rather than surfacing the gap. Fixed: added
  `_execution_id_or_fallback(rel_path, execution_id)`, applied at all
  three `SlugMatch` construction sites (local parse-failure, local
  success, remote), falling back to the filename stem — always present,
  and exactly what `execution_id` is supposed to equal by convention —
  instead of an empty string. Test:
  `test_missing_execution_id_falls_back_to_filename_stem`.
- **Codex: "Avoid classifying cat-file failures by one diagnostic"**
  (valid, fixed — a genuine refinement of round 2's own fix, not just a
  new bug): round 2 distinguished a legitimate "path absent" `cat-file
  -e` outcome from a real git failure by matching stderr against "does
  not exist in". Codex found (and verified against git 2.43.0) that git
  uses a *different* wording — "exists on disk, but not in" — for the
  specific case where a path is present on disk/in the worktree but
  absent from the tree-ish being checked; matching only one wording
  misclassified the other as a fatal error, incorrectly failing the
  whole check (exit 3) for what was actually a valid new match. Rather
  than add a second regex (still fragile — free-text git messages aren't
  a stable API, evidently varying by exactly *how* a path is absent),
  replaced the entire `cat-file -e` + stderr-matching approach with a
  structural `git ls-tree --name-only <merge_base> -- <path>` check:
  success with empty stdout means "absent at that tree" (safe to treat
  as a new match), success with non-empty stdout means "present"
  (inherited), and failure means the tree-ish itself is unusable (a
  genuine error, correctly raised). No free-text message is inspected at
  all, so there's no wording to misclassify. Removed the now-unused
  `_CAT_FILE_MISSING_PATTERN`. Tests:
  `test_merge_base_tree_check_failure_raises_not_treated_as_not_inherited`
  (renamed/updated from the old cat-file-specific test),
  `test_path_present_on_disk_but_absent_from_merge_base_tree_is_new_match`.
- **Not new work — stale/duplicate threads, left alone:** all other
  visible threads (project-root binding, unparseable-match preservation,
  unresolved-recency blocking, force-push test coverage, timestamp-tie
  blocking, offset-naive timestamps, base-ref refspec, TZ test
  portability) are round-1 through round-5 findings already fixed in
  code in prior commits on this branch, still open only because
  `/lrh-confirm-fixes` (not `/lrh-review-response`) resolves GitHub
  review threads, later in the `/lrh-land` chain.

# Validation

- `pytest tests/` — 835 passed (up from 833; +2 net tests), same 1
  pre-existing unrelated failure as before this PR
  (`version_integration_test.py`).
- `pytest tests/assist_tests/prompt_workflow_slug_test.py` — 27 passed.
- `scripts/format --check` / `scripts/lint` — clean.
- `lrh validate` — 0 errors, 1 pre-existing unrelated warning.

# Follow-up

Per explicit user direction, this is the last auto-fixed round; reporting
back to the user now with the full round-by-round summary regardless of
outcome, rather than continuing to auto-fix further rounds.
