---
execution_id: 2026_08_02_13_49_25_SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS_REVIEW
prompt_id: PROMPT(AD_HOC:SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS_REVIEW)[2026-08-02T13:49:16+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_08_02_06_19_59_SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/443
commit: 
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/443
session_transcript: claude-app:3fcab22f-9ebe-4392-bf31-2103fce507f2
created_at: 2026-08-02T13:49:25+00:00
---

# Summary

Review-response round addressing 4 findings surfaced on the `_CONFIRM`
commit itself (`a27b351`) — exactly the risk `/lrh-confirm-fixes` Step 8
warns about: automated reviewers retriggered on a `_CONFIRM` push can
still find real issues, even after 9 prior clean-verification rounds.
2 formal Codex threads, 2 Copilot "suppressed" (low-confidence,
non-blocking) review-body comments — all 4 verified valid before fixing.

# Result

- **Codex: "Derive local fallback before coercing execution IDs"**
  (valid, fixed): `find_local_matches` passed the already-coerced
  `record.execution_id` (a plain `str`, because
  `prompt_workflow_records._frontmatter_string` converts any non-string
  YAML scalar via `str(value)`) into `_execution_id_or_fallback`, whose
  `isinstance(..., str)` check could no longer distinguish a genuinely
  authored ID from a coerced `execution_id: 123`. The remote path
  (`parse_front_matter_fields_from_text`) drops non-string fields
  entirely and already fell back correctly — the two paths disagreed.
  Fixed: added `_raw_execution_id_or_blank(frontmatter)`, which checks
  the *raw*, uncoerced frontmatter mapping's type instead, and wired it
  into `find_local_matches`. Test:
  `test_non_string_execution_id_falls_back_to_filename_stem`.
- **Codex: "Handle a missing git executable as a slug-check failure"**
  (valid, fixed): `_run_git_or_raise` had no handling for
  `FileNotFoundError` (raised directly by `subprocess.run` when the
  executable itself can't be launched, e.g. `git` missing from `PATH`) —
  unlike the adjacent `gh_client.run_gh_json`, which already catches this
  exact failure mode. Fixed: wrapped the `git_runner(args)` call in
  `_run_git_or_raise` with a `try/except FileNotFoundError`, converting
  it to `SlugCheckError` like every other git failure in this module.
  Test: `test_missing_git_executable_raises_slug_check_error_not_traceback`.
- **Copilot (suppressed, low-confidence): mutual-exclusivity check uses
  truthiness** (valid, fixed): `bool(args.prompt_id) == bool(args.slug)`
  treated `--slug ""` the same as "not provided," routing it into the
  generic "requires exactly one" error instead of `normalize_slug`'s more
  specific validation. Fixed: changed to `(args.prompt_id is None) ==
  (args.slug is None)` — presence, not truthiness. Test:
  `test_lrh_prompt_check_execution_empty_slug_hits_slug_validator`.
- **Copilot (suppressed, low-confidence): `_list_open_prs` doesn't fail
  loudly on a malformed `gh` payload entry** (valid, fixed): a
  non-dict entry was silently skipped, and `int(entry["number"])`/
  `entry["baseRefName"]` on a dict entry could raise a raw
  `KeyError`/`TypeError`/`ValueError` instead of the documented
  `SlugCheckError` contract this whole PR is built around. Fixed: both
  cases now raise `SlugCheckError` with the offending entry included.
  Test: `test_malformed_gh_pr_list_entry_raises_not_silently_dropped`
  (covers a missing field, a wrong-typed field, and a non-dict entry).

# Validation

- `pytest tests/` — 849 passed (up from 845; +4 new tests), 0 failed.
- `pytest tests/assist_tests/prompt_workflow_slug_test.py
  tests/cli_tests/prompt_test.py` — 55 passed.
- `scripts/format --check` / `scripts/lint` — clean.
- `lrh validate` — 0 errors, 1 pre-existing unrelated warning.

# Follow-up

None beyond what the primary record already tracks. Per the standing
`/lrh-confirm-fixes` Step 8 contract, this new `_CONFIRM`-commit-push
requires a fresh CI re-check and REVIEW-LANDED pass on its own resulting
`HEAD` before any merge verdict.
