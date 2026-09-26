---
execution_id: 2026_09_26_01_36_35_WI_LRH_CONSOLE_DESKTOP_PROTOCOL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_PROTOCOL_REVIEW)[2026-09-26T01:33:09+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_09_26_00_44_44_WI_LRH_CONSOLE_DESKTOP_PROTOCOL_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/727
commit: 
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/727"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-09-26T01:36:35+00:00
---

# Summary

This is review-response round 4 for PR #727. The confirm-fixes round-3
Step 8 substitute cold review on HEAD `84cd0e17` judged the PR safe to merge
and reported one low-severity finding. The user chose to fix it before the
merge gate. This is a same-run continuation of the round-3 `_REVIEW` record.

# Result

The finding was re-verified directly:
`resolve_workspace('/' + 'a'*300)` raised a raw `OSError` (Errno 63,
`File name too long`). The error escaped `run_session` and the child reported
an uncorrelated `internal_error`.

The fix is in commit `5d0050e9`:

- `resolve_workspace` wraps its filesystem checks. `OSError` and `ValueError`
  (for example ENAMETOOLONG, EACCES, or an embedded NUL) become a correlated
  `invalid_workspace`.
- `run_session` also reports any other unexpected error during
  start-request handling as `internal_error` carrying the correlated launch
  ID.
- The docs' error-code table is updated, and there are 3 new unit tests.

End to end, a real child given `"/" + "a" * 300` now returns
`invalid_workspace` for launch `L`.

# Validation

- `scripts/format --check --diff`: 261 files unchanged. `scripts/lint`: exit 0.
- `scripts/test --log`: `Ran 1781 tests in 117.406s`, OK.
- `lrh validate`: 0 errors, 0 warnings.
- Desktop suites: 84 tests OK (48 protocol unit, 15 supervisor unit, 21
  smoke). No `ResourceWarning`s.

# Follow-up

A confirm-fixes/REVIEW-LANDED pass on the new HEAD follows.
