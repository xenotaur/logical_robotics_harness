---
execution_id: 2026_08_02_06_03_18_SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS_REVIEW
prompt_id: PROMPT(AD_HOC:SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS_REVIEW)[2026-08-02T06:03:05+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_07_31_20_54_04_SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/443
commit: 
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/443
session_transcript: claude-app:3fcab22f-9ebe-4392-bf31-2103fce507f2
created_at: 2026-08-02T06:03:18+00:00
---

# Summary

Fix round on PR #443 driven by a fresh independent subagent review
(cold-context, general-purpose agent given the PR diff and background
context but no session memory) rather than a Codex/Copilot bot retrigger
— the round-7 bot retrigger never actually landed (interrupted mid-flow
by an unrelated Bash-tool transient failure, then the session moved to
resolving a `main`-worktree lock for the user before returning to this
PR). Per user direction, dispatched the subagent instead of retriggering.
It found 4 new findings not covered by rounds 1-7; user approved fixing
all 4.

# Result

- **(P2) Single unreachable/broken open PR aborted remote slug discovery
  for every other PR and every slug** (valid, fixed): `find_remote_matches`
  unconditionally fetched each open PR's base ref and computed
  `merge-base` before checking whether that PR's tree even contained a
  candidate file, so a single open PR with a deleted/unfetchable base
  branch (a real, if uncommon, occurrence for a long-open PR) made
  `lrh prompt check-execution --slug <anything>` fail loudly (exit 3)
  repo-wide, for every slug, regardless of relevance. Fixed: reordered
  the loop to list each PR's tree (`git ls-tree -r <pr_ref>`, already
  required and always resolvable once the PR ref itself is fetched) and
  filter to trailing-segment matches *before* touching that PR's base
  ref at all; the base-ref fetch/merge-base calls now only run for a PR
  that actually contains a candidate match, so a broken base ref on an
  unrelated PR never blocks discovery for other PRs or other slugs.
  Fail-loud semantics are preserved exactly where they're needed (a PR
  that might genuinely hide a match). Test:
  `test_unrelated_pr_with_broken_base_ref_does_not_abort_discovery`
  (real git simulation: PR#3 has unrelated content and a nonexistent base
  branch; PR#1's genuine match is still found without error).
- **(P3) Zero CLI-level test coverage for `--slug` mode** (valid, fixed):
  added 5 subprocess-level tests to `tests/cli_tests/prompt_test.py`
  covering the mutual-exclusivity check (neither/both of
  `--prompt-id`/`--slug`), malformed `--slug` input, no-match (exit 0),
  and a blocking match (exit 1) — exercising `run_prompt_cli`'s actual
  argparse wiring end-to-end, not just the library functions underneath.
- **(P3) Undocumented exit code 2** (valid, fixed): added a `2` bullet
  (malformed input / usage error, distinct from a slug-check result) to
  the "interpret the exit code" section in all 5 migrated skill docs
  (`lrh-proposal`, `lrh-work-item`, `lrh-workstream`,
  `lrh-review-response`, `lrh-confirm-fixes`) and the 3
  `references/execution-record.md` condensed copies. All `.claude/skills/`
  mirrors synced.
- **(P3) Case-sensitive trailing-segment match, unlike the shell logic it
  replaced** (valid, fixed): `_trailing_segment_pattern` now compiles
  with `re.IGNORECASE`, matching the `grep -i` behavior of the shell
  check this module replaced — a non-canonically-cased filename that
  used to match under the old logic now matches again. Test:
  `test_matches_are_case_insensitive_like_the_shell_check_it_replaced`.

# Validation

- `pytest tests/` — 844 passed, 0 failed (the previously-noted
  pre-existing unrelated `version_integration_test.py` failure did not
  reproduce in this worktree's build).
- `pytest tests/assist_tests/prompt_workflow_slug_test.py` — 30 passed.
- `pytest tests/cli_tests/prompt_test.py` — includes the 5 new `--slug`
  CLI-level tests, all passing.
- `scripts/format --check` / `scripts/lint` — clean.

# Follow-up

None beyond what the primary record already tracks.
