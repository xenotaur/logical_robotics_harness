---
execution_id: 2026_08_02_15_03_56_SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS_REVIEW
prompt_id: PROMPT(AD_HOC:SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS_REVIEW)[2026-08-02T15:03:40+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_08_02_13_49_25_SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/443
commit: b2ae5602797364c43eeb6264375d9a596d4e1d32
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/443
session_transcript: claude-app:3fcab22f-9ebe-4392-bf31-2103fce507f2
created_at: 2026-08-02T15:03:56+00:00
---

# Summary

Review-response round following the `_CONFIRM` commit's own review (per
Step 8's explicit warning that a `_CONFIRM` push can itself surface real
findings). Codex and Copilot both reviewed at commit `255111e`. 5 new
genuine findings; remaining threads are stale duplicates of already-fixed
prior-round issues awaiting the next `/lrh-confirm-fixes` pass.

# Result

- **Codex: "Store pull refs outside remote-tracking namespaces"** (valid,
  fixed): `refs/remotes/pr/<N>`/`refs/remotes/pr-base/<N>` could collide
  with a client repo's own real remote literally named `pr`/`pr-base`
  (uncommon but real), and nothing cleaned these refs up afterward,
  leaving misleading branches behind on every check regardless. Fixed:
  moved to a harness-owned namespace, `refs/lrh/pulls/<N>/head` and
  `refs/lrh/pulls/<N>/base`, which cannot collide with any configured
  remote's own tracking refs; wrapped each PR's per-iteration work in a
  `try/finally` that deletes both refs via `_delete_ref_best_effort`
  afterward. Caught my own regression while implementing this: the first
  version called `git_runner(["update-ref", "-d", ref])` directly in the
  `finally` block with no exception handling, which meant a scenario
  where `git` itself is missing (the `test_missing_git_executable_*`
  case) had its cleanup call *also* raise `FileNotFoundError`, masking
  the real `SlugCheckError` the primary code path had already raised.
  Caught by actually running the existing test suite, not just reasoning
  about it — `_delete_ref_best_effort` now swallows every exception from
  the cleanup call, since cleanup failure (including "ref was never
  created" in the no-candidates early-exit path) must never mask or
  replace whatever the real check's own outcome was.
- **Codex: "Move the real Git simulation to the smoke tier"** (valid,
  fixed): `CrossPrDiscoveryGitSimulationTest` launched many real `git`
  subprocesses and built/fetched from a real Git remote inside
  `tests/assist_tests/`, which `scripts/test` (the normal, supposedly
  hermetic unit suite) runs on every invocation — violating AGENTS.md's
  "keep unit tests fast, deterministic, and hermetic... avoid
  Git remotes... in the normal unit suite" rule. Moved the class (renamed
  `CrossPrDiscoveryGitSimulationTests`) to
  `tests/smoke/prompt_workflow_slug_cross_pr_smoke.py`, run via
  `scripts/smoke`, not `scripts/test`. The 3 tests that never actually
  reach a real `git`/`gh` call (empty PR list, malformed-payload
  rejection, and the fake missing-git-executable case) stayed in
  `tests/assist_tests/prompt_workflow_slug_test.py` as a new
  `SlugRemoteMatchesRunnerErrorHandlingTest` class, since they're already
  genuinely hermetic. Confirmed via `scripts/test`'s discovery pattern
  (`*_test.py`) correctly excludes the new `*_smoke.py` file, and
  `python -m unittest discover -s tests/smoke -p "*_smoke.py"` correctly
  includes and passes all 9 relocated tests.
- **Codex: "Update the execution record to the final status policy"**
  (valid, fixed): this PR's own primary execution record's "Explicitly
  not touched" bullet still said the `planned`-status gap was "left
  non-blocking by default" — accurate against an early round's
  implementation, but a later round changed `SlugCheckResult.blocking` to
  block on anything except the three explicit terminal statuses, so
  `planned` now blocks too. Corrected the record's body (still open for
  editing — this PR hasn't merged yet, so this is normal same-PR
  authoring, not a violation of the body-immutability rule that applies
  post-merge) with an explicit correction note, rather than silently
  rewriting history.
- **Copilot: Windows backslash path-separator bug (2 suppressed comments,
  same root cause at two call sites)** (valid, fixed): both
  `rel_prefix`/`bucket_prefix` were built via
  `pathlib.PurePosixPath(str(output_root))`, which does not treat
  backslash as a separator at all — a Windows-native `--output-root`
  value (e.g. `project\executions`) would produce a single malformed
  path segment instead of proper components, breaking git pathspec
  comparisons (which always expect forward slashes) and local/remote
  match de-duplication. Fixed both sites to normalize through the
  platform-native `pathlib.PurePath(output_root).as_posix()` first,
  converting any native separator correctly, before wrapping the result
  in `PurePosixPath` for POSIX-style joining.

- **Not new work — stale/duplicate threads, left alone:** the remaining
  visible threads are findings from prior rounds already fixed in code in
  earlier commits on this branch, still open only because
  `/lrh-confirm-fixes` (not `/lrh-review-response`) resolves GitHub
  review threads — the next confirm-fixes pass will re-verify and resolve
  everything still open, including this round's 5 fixes.

# Validation

- `pytest tests/` — 839 passed (up from prior rounds), same 1
  pre-existing unrelated failure as before this PR
  (`version_integration_test.py`).
- `pytest tests/assist_tests/prompt_workflow_slug_test.py` — 25 passed,
  now in 0.04s (down from ~5s) after the smoke-tier move.
- `pytest tests/smoke/prompt_workflow_slug_cross_pr_smoke.py` — 9 passed.
- `python -m unittest discover -s tests/smoke -p "*_smoke.py"` — the 9
  relocated tests all pass; the only 2 failures in that run are
  pre-existing, unrelated smoke tests (`prompt_cli_install_smoke.py`,
  `version_install_smoke.py`) failing on venv/wheel-build steps specific
  to this sandbox environment, confirmed unrelated to this PR's changes.
- `scripts/format --check` / `scripts/lint` — clean.
- `lrh validate` — 0 errors, 1 pre-existing unrelated warning.

# Follow-up

None beyond what the primary record already tracks.
