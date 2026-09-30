---
execution_id: 2026_09_30_02_35_16_WI_LRH_CONSOLE_DESKTOP_SUPERVISOR_CONFIRM
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_SUPERVISOR_CONFIRM)[2026-09-30T02:35:16+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_09_29_23_50_43_WI_LRH_CONSOLE_DESKTOP_SUPERVISOR
pr: https://github.com/xenotaur/logical_robotics_harness/pull/758
commit: 6977ce4637d32f5865b2e87ebba75a5535021113
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/758"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-09-30T02:35:16+00:00
---

# Summary

`/lrh-confirm-fixes` for PR #758 (`WI-LRH-CONSOLE-DESKTOP-SUPERVISOR`), run
against HEAD `3af9cc4b` after review-response round 1 (`7dcbe02b`) and the
fix for the macOS startup stall (`1c331d7e`).

# Result

- **Threads.** The authoritative list has 4 threads, and none are unresolved.
  - I checked each one against the diff, found each Clear-satisfied, and
    resolved it with `resolveReviewThread`:
    - Codex P1, `refresh()` handles `noticed_earlier`: satisfied.
    - Codex P2, `start()` coalesces through `arrived_during_launch` and the
      generation: satisfied.
    - Copilot: the bounded `Inbox` and event history are in the diff.
    - Copilot: `HelperGuard` is in the diff.
  - Regression tests cover both Codex fixes.
- **Substitute cold review on `3af9cc4b`.** Verdict: safe to merge, with no
  blocking findings.
  - It re-ran `serve_test` (68 tests) and `cargo test --locked` (14 unit and
    17 integration tests).
  - It confirmed these are sound:
    - the lock ordering;
    - the Inbox, including Condvar handling, the non-blocking reader, and
      EOF always arriving last;
    - the `serve.py` change for IPv4 and IPv6, which nothing reads
      `server_name` from;
    - the `-c` wrapper's argv.
  - Its non-blocking items are deferred:
    - (low) A Start queued behind a failing launch can return that
      launch's error even if a Stop ran in between.
    - (low) A narrow race: a Restart whose child crashes before the queued
      Start acquires the lock makes that Start return `ExitedUnexpectedly`.
    - (nit) A backend that writes more than 256 lines before the first read
      loses its first line.
    - (nit) The test-only `dump_traceback_later(12)` is never cancelled.
- **CI on `3af9cc4b`: all 7 checks green.** That includes
  `desktop (macos-latest)`, where the supervisor tests pass 17/17 in 5.09 s
  and were timing out at 25 s before the reverse-DNS fix. It also includes
  `desktop (ubuntu-latest)`, `tests`, `coverage`, `lint`,
  `installed-wheel-smoke`, and the workflow check.
- **Hosted review bots** reviewed the first push only. Later HEADs use
  substitute cold reviews.
- **Verdict: green.** REVIEW-LANDED is still pending for the commit that
  carries this record.

# Validation

- `lrh validate`: 0 errors, 0 warnings, before commit.

# Follow-up

The single merge-and-closeout request comes next. Merging resolves
`WI-LRH-CONSOLE-DESKTOP-SUPERVISOR`.
