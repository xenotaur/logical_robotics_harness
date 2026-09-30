---
execution_id: 2026_09_30_00_19_16_WI_LRH_CONSOLE_DESKTOP_SUPERVISOR_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_SUPERVISOR_REVIEW)[2026-09-30T00:19:16+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/758
commit: 
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/758"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-09-30T00:19:16+00:00
---

# Summary

Review-response round 1 for PR #758 (`WI-LRH-CONSOLE-DESKTOP-SUPERVISOR`), run
within `/lrh-execute` → `/lrh-land`.

- CI `desktop (macos-latest)` failed on the first push, which fired the
  stop-work condition. The failure: 5 real-backend supervisor tests on the
  repository workspace timed out at 20 s with an empty stderr tail.
- The hosted reviews left 4 inline threads.
- The user chose to fix everything in this PR as proposed: first push
  diagnostics, then fix the root cause, and fix all 4 threads.

# Result

`7dcbe02b` fixes all 4 threads:

1. **Codex P1: an exit discovered by `ping()` never reached `status()`.**
   - `refresh()` now also marks a launch failed when the server already
     knows it failed but the status still says Running.
   - `Supervisor::ping` refreshes after the ping.
   - Regression test: `an_exit_found_by_ping_is_reflected_in_status`.
2. **Codex P2: a Start that waited behind a failing launch launched again.**
   - Start now records whether a launch was in flight, or the generation
     changed, before it queues on the lock. If so, it returns that launch's
     outcome instead of launching.
   - Regression test: `a_start_during_a_failing_launch_does_not_launch_again`,
     which counts launches through a file. Its first version caught a gap in
     the initial fix: a Start that arrived after the generation bump still
     relaunched.
3. **Copilot: an unbounded post-ready queue and event histories.**
   - The mpsc channel is replaced by a bounded `Inbox` (256 items) that
     drops the oldest items. The reader never blocks, so the child's stdout
     is always drained.
   - `events` and `stale_events` are bounded at 256.
   - Unit tests cover both bounds.
4. **Copilot: the parent-loss helper could leak on an early failure.** A
   `HelperGuard` now kills and reaps it on every exit path.

The same commit adds test-only CI diagnostics:

- Real backends launch through
  `faulthandler.dump_traceback_later(12, exit=False)`, so a stall before
  `ready` puts all thread stacks in the stderr tail.
- `start_real` reports the start duration and that stderr tail when a start
  fails.

The macOS root cause is still open and waits on the next CI run.

# Validation

- `cargo test --locked` passed three consecutive runs (14 unit and 17
  integration tests each), leaving no stray processes.
- `scripts/format --check --diff --desktop`, `scripts/lint --desktop`,
  `scripts/test --desktop`, `lrh validate`, and `scripts/check-workflows` all
  pass.

# Follow-up

- Read the macOS CI diagnostics, fix the stall's root cause, and then run
  confirm-fixes.
