---
execution_id: 2026_08_02_06_19_59_SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS_REVIEW
prompt_id: PROMPT(AD_HOC:SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS_REVIEW)[2026-08-02T06:19:48+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_08_02_06_03_18_SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/443
commit: ac4822165df35ffdd6ba0782f6654dbcb4e4c30d
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/443
session_transcript: claude-app:3fcab22f-9ebe-4392-bf31-2103fce507f2
created_at: 2026-08-02T06:19:59+00:00
---

# Summary

Review-response round following the subagent-review fix round. Codex
reviewed at commit `fe21289`. 2 new genuine findings; remaining threads
are stale duplicates of already-fixed rounds 1-7 plus the subagent round.

# Result

- **Codex: "Paginate beyond the first 1,000 open PRs"** (valid, fixed):
  `_list_open_prs` hardcoded `--limit 1000`. `gh pr list --limit N`
  paginates internally to satisfy any requested N, so this wasn't a real
  API constraint, just an arbitrary cap that would silently omit PRs in a
  repo with more than 1,000 legitimately open PRs — and since the list is
  authoritative for the slug check, a blocking match hiding past the
  cutoff would produce a false "no prior record" (exit 0). Fixed: raised
  the limit to `_MAX_OPEN_PRS_TO_SCAN = 100_000`, a value effectively
  unbounded for any plausible repo size. Test:
  `test_gh_pr_list_requests_far_beyond_a_realistic_open_pr_count`.
- **Codex: "Make the UTC test exercise local conversion"** (valid, fixed
  — a real bug in this session's own round-5 test rewrite, not the
  production code): the round-5 `_FrozenDatetime.now(tz)` mock forwarded
  its `tz` argument into `fixed_instant.astimezone(tz)`, so on a
  UTC-configured host (common in CI) the *removed* buggy production
  code's trailing bare `.astimezone()` call would *also* have been a
  no-op — meaning the regression test could pass even against the exact
  bug it was written to catch, purely because of the test-runner's own
  system timezone. Fixed properly, and **verified empirically rather than
  just reasoned about**: rewrote the mock so `now()` returns a genuine
  `_FrozenDatetime` instance (constructed via `cls(...)`, not the plain
  `datetime.datetime(...)` constructor — a first attempt at this fix
  still didn't work, confirmed by directly testing it standalone: the
  returned object wasn't actually an instance of the subclass, so the
  `astimezone` override silently never applied) with a separately
  overridden `astimezone()` that returns a deliberately different,
  deterministic sentinel value when called with no argument (the buggy
  code's exact call shape) regardless of host timezone. Then proved the
  fix both ways by temporarily reintroducing the exact removed bug
  (`.astimezone()` with no args) directly in `prompt_workflow.py` and
  confirming the test now fails against it, then restored the correct
  code and confirmed the test passes again.

# Validation

- `pytest tests/assist_tests/prompt_workflow_test.py
  tests/assist_tests/prompt_workflow_slug_test.py` — 38 passed.
- `pytest tests/` (full suite) — 845 passed, 0 failed.
- Manual verification of the UTC test fix: reintroduced the exact removed
  bug in `prompt_workflow.py`, confirmed
  `test_label_timestamp_is_utc_regardless_of_local_timezone` fails
  against it (wrong filename/prompt_id, `2020-01-01` sentinel value
  surfaced instead of the correct fixed instant), restored the fix,
  confirmed the test passes again.
- `scripts/format --check` / `scripts/lint` — clean.

# Follow-up

None beyond what the primary record already tracks.
