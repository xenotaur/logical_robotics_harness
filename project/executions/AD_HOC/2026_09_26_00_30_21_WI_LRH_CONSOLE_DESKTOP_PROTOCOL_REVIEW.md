---
execution_id: 2026_09_26_00_30_21_WI_LRH_CONSOLE_DESKTOP_PROTOCOL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_PROTOCOL_REVIEW)[2026-09-26T00:24:57+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_09_25_21_58_23_WI_LRH_CONSOLE_DESKTOP_PROTOCOL_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/727
commit: 
created_at: 2026-09-26T00:30:21+00:00
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/727"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
---

# Summary

This is review-response round 2 for PR #727. `/lrh-confirm-fixes` Step 8 ran
a substitute PR-mode cold review against HEAD `50efc240`. The review judged
the PR safe to merge but reported four low-severity, non-thread findings. The
user chose to fix all four before the merge gate. This round is a same-run
continuation of the round-1 `_REVIEW` record (`in_progress`, authored earlier
in this same `/lrh-land` run).

# Result

The top finding was re-verified directly: a 65,293-byte valid start request
produced `failed internal_error`. All four findings were fixed in commit
`3a874879`, plus a PR-description edit:

1. **Oversized `ready` from a long valid path.** `parse_start_request` now
   rejects `workspace.project_root` over 4,096 UTF-8 bytes as
   `invalid_workspace` (correlated launch ID, exit 3). The same request now
   yields `failed invalid_workspace` for launch `L`. Covered by a unit test.
2. **Doc exit-code sentence.** It now includes exit 1 for `internal_error`.
   The 4,096-byte limit is documented in the start-request table and the
   error-code table.
3. **Stale PR description counts.** Refreshed to 44/14 unit, 21 smoke, and
   1,776 total, and it now summarizes both review rounds.
4. **Example supervisor traceback.** `main()` now emits a JSON `failed` event
   (`SupervisorError`, or `health_check_failed` for `OSError`/HTTP errors)
   after the `finally` stop, and exits 1. Covered by a unit test.

# Validation

- `scripts/format --check --diff`: 261 files unchanged. `scripts/lint`: exit 0.
- `scripts/test --log`: `Ran 1776 tests in 121.393s`, OK.
- `lrh validate`: 0 errors, 0 warnings.
- Desktop suites: 79 tests OK (44 protocol unit, 14 supervisor unit, 21
  smoke). No `ResourceWarning`s.
- `scripts/smoke`: 33 tests, with 1 failure in the pre-existing, unrelated
  `prompt_cli_install_smoke` (a `--no-deps` wheel lacks `yaml`). All desktop
  smoke tests passed.

# Follow-up

A confirm-fixes/REVIEW-LANDED pass on the new HEAD follows.
