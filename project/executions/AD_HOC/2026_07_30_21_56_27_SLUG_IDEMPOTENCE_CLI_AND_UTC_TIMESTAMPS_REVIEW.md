---
execution_id: 2026_07_30_21_56_27_SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS_REVIEW
prompt_id: PROMPT(AD_HOC:SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS_REVIEW)[2026-07-30T21:56:20+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_07_30_21_38_31_SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/443
commit: 
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/443
session_transcript: claude-app:3fcab22f-9ebe-4392-bf31-2103fce507f2
created_at: 2026-07-30T21:56:27+00:00
---

# Summary

Round 2 review response for PR #443. Codex and Copilot both reviewed
HEAD `b560666`. 3 new genuine findings; 2 duplicate/stale threads for
already-fixed round-1 issues (still open only because thread resolution
is `/lrh-confirm-fixes`'s job, not `/lrh-review-response`'s).

# Result

- **Codex: "Block when a match has unknown recency"** (valid, fixed): a
  match with missing/malformed `created_at` sorted as the oldest possible
  instant, a pure tiebreak -- but this let it silently *lose* the
  most-recent comparison to an older-but-parseable terminal match,
  causing the overall check to report non-blocking (exit 0) even when
  the truly-latest attempt (the one with unknown recency) might be
  `in_progress`/`landed`. Fixed: added `SlugMatch.has_known_created_at`
  and `SlugCheckResult.has_unresolved_recency`; `blocking` now returns
  true whenever *any* match's recency can't be established, regardless
  of what the naive timestamp-max comparison would otherwise pick.
  `format_text_result` reports this case distinctly ("BLOCKING
  (unresolved recency)"). This also folds in and generalizes round 1's
  "preserve unparseable matches" fix, since a synthetic `status:
  unparseable` match now always has an empty/unresolvable `created_at`
  too. Tests:
  `test_unresolved_recency_blocks_even_if_naive_pick_is_terminal`,
  `test_all_matches_have_known_recency_is_not_flagged_unresolved`.
- **Copilot: `cat-file -e` return code not fully validated** (valid,
  fixed): any nonzero exit from `git cat-file -e <merge_base>:<path>` was
  treated as "not inherited, proceed as a genuine new match" -- correct
  for git's ordinary "path doesn't exist at this tree" outcome, but wrong
  for a genuine git failure (corrupted repo, bad object database), which
  would then be silently misreported as a real match instead of failing
  loudly. Fixed: added `_CAT_FILE_MISSING_PATTERN` to distinguish git's
  standard "does not exist in" message from anything else; only the
  former is treated as "not inherited," anything else raises
  `SlugCheckError`. Test:
  `test_cat_file_unexpected_failure_raises_not_treated_as_not_inherited`.
- **Copilot: UTC regression test only checked `prompt_id`'s offset, not
  the actual filename** (valid, fixed): the round-1 test asserted
  `prompt_id`'s ISO offset was always `+00:00` across TZ settings, but
  the bug being fixed was in the *offset-free* `strftime`-based outputs
  (`execution_id`/filename), formatted independently from `prompt_id`'s
  `isoformat()`. As written, the test could pass even if the filename
  timestamp regressed to local time while `prompt_id` stayed correct.
  Fixed: froze the clock to a known instant (`unittest.mock.patch` on
  `lrh.prompt_workflow.datetime.datetime`) and asserted the actual
  `suggested_execution_file` segment matches the fixed instant's UTC
  wall-clock value identically across two different `TZ` settings.
- **Copilot: no test for the force-refspec fetch** (valid, added new
  coverage): added
  `test_force_pushed_pr_head_is_picked_up_not_left_stale`, which fetches
  a PR ref once, force-amends the origin's PR branch (simulating a real
  force-push, a non-fast-forward rewrite), force-moves
  `refs/pull/<N>/head` to it, and asserts a second `find_remote_matches`
  call picks up the rewritten content rather than the stale
  previously-fetched commit.
- **Not new work — stale/duplicate threads, left alone:** two Codex
  comments ("Run remote discovery against the requested project root",
  "Preserve filename matches whose records fail to parse") are the exact
  same review threads as round 1 (identical comment IDs), already
  addressed by round-1's commit. They remain open only because
  `/lrh-review-response` doesn't resolve GitHub review threads --
  `/lrh-confirm-fixes` (Step 5 of `/lrh-land`) does that via
  `resolveReviewThread`, later in the chain.

# Validation

- `pytest tests/` — 829 passed (up from 825; +4 new tests), same 1
  pre-existing unrelated failure as before this PR.
- `pytest tests/assist_tests/prompt_workflow_slug_test.py` — 21 passed.
- `pytest tests/assist_tests/prompt_workflow_test.py` — 7 passed.
- `scripts/format --check` / `scripts/lint` — clean.
- `lrh validate` — 0 errors, 1 pre-existing unrelated warning.

# Follow-up

None beyond what the primary record already tracks.
