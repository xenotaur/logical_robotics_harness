---
execution_id: 2026_09_26_00_44_44_WI_LRH_CONSOLE_DESKTOP_PROTOCOL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_PROTOCOL_REVIEW)[2026-09-26T00:40:48+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_09_26_00_30_21_WI_LRH_CONSOLE_DESKTOP_PROTOCOL_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/727
commit: d9f0e49e722a2b940ac62fe8e943a2c814e9315a
created_at: 2026-09-26T00:44:44+00:00
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/727"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

This is review-response round 3 for PR #727. The confirm-fixes round-2
Step 8 substitute cold review on HEAD `9cf9ecbf` judged the PR safe to merge
and reported two low-severity, non-thread findings. The user chose to fix
both before the merge gate. This is a same-run continuation of the round-2
`_REVIEW` record.

# Result

The invoking session confirmed both findings by reading the code. Both were
fixed in commit `a2b4ae5c`:

1. **Example exits 0 on a non-200 `/health`.** `desktop_supervisor.main()`
   now raises `health_check_failed` for any non-200 status, which is emitted
   as JSON `failed` after the child is stopped (exit 1). Covered by a unit
   test.
2. **Byte cap not applied to the resolved path.** `resolve_workspace` now
   rejects a resolved path over `MAX_WORKSPACE_PATH_BYTES` as
   `invalid_workspace`. A symlink unit test covers it, and the doc's
   error-code table was updated.

The evidence record and the PR description were refreshed with the round-3
results.

# Validation

- `scripts/format --check --diff`: 261 files unchanged. `scripts/lint`: exit 0.
- `scripts/test --log`: `Ran 1778 tests in 118.291s`, OK.
- `lrh validate`: 0 errors, 0 warnings.
- Desktop suites: 81 tests OK (45 protocol unit, 15 supervisor unit, 21
  smoke). No `ResourceWarning`s.
- `python -m lrh.desktop_supervisor --lrh-executable "$(command -v lrh)" --project-root .`:
  ready, health 200, ping ok, stopped, exit 0.

# Follow-up

A confirm-fixes/REVIEW-LANDED pass on the new HEAD follows.
