---
execution_id: 2026_09_26_01_57_27_WI_LRH_CONSOLE_DESKTOP_PROTOCOL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_PROTOCOL_REVIEW)[2026-09-26T01:53:47+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_09_26_01_36_35_WI_LRH_CONSOLE_DESKTOP_PROTOCOL_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/727
commit: d9f0e49e722a2b940ac62fe8e943a2c814e9315a
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/727"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-09-26T01:57:27+00:00
---

# Summary

This is review-response round 5 for PR #727. The confirm-fixes round-4
Step 8 substitute cold review on HEAD `e7a46f2a` judged the PR safe to merge
and reported one low-severity finding. The user chose to fix it, then go to
the merge gate unless the next review finds something above low severity.
This is a same-run continuation of the round-4 `_REVIEW` record.

# Result

The finding was re-verified directly. In-process, a `RuntimeError` from the
server factory escaped `run_session` and nothing was written. That
contradicts the doc row saying `internal_error` carries the launch ID once
`start` is read.

The fix is in the `fix(serve): correlate every pre-ready failure` commit. One
handler now covers everything from reading `start` to sending `ready`. It
stops a started server (or closes an unstarted one) and reports
`internal_error` with the request's launch ID (exit 1). There are 2 new tests:
a broken factory, and a failing self-check with the socket confirmed closed.

The reviewer's informational note — EACCES inside the workspace now maps to
`invalid_workspace` — matches the documented wording. No change was needed.

# Validation

- `scripts/format --check --diff`: 261 files unchanged. `scripts/lint`: exit 0.
- `scripts/test --log`: `Ran 1783 tests in 116.080s`, OK.
- `lrh validate`: 0 errors, 0 warnings.
- Desktop suites: 86 tests OK (50 protocol unit, 15 supervisor unit, 21
  smoke). No `ResourceWarning`s.

# Follow-up

A confirm-fixes/REVIEW-LANDED pass on the new HEAD follows, then the merge
gate.
