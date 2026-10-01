---
execution_id: 2026_10_01_02_48_39_WI_LRH_CONSOLE_DESKTOP_SHELL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_SHELL_REVIEW)[2026-10-01T02:48:39+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/762
commit: 
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/762"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-10-01T02:48:39+00:00
---

# Summary

Review-response round 1 for PR #762 (`WI-LRH-CONSOLE-DESKTOP-SHELL`), run
within `/lrh-execute` → `/lrh-land`.

CI on the first push was 7/7 green, including both desktop jobs. The
first-push hosted reviews left 3 inline threads: 1 from Codex and 2 from
Copilot. The user chose to fix two of them and resolve the third as already
satisfied.

# Result

1. **Codex P2: the shutdown latch was set only after taking the operation
   lock.** A queued Start or Restart could win the lock first and launch after
   Quit.
   - Fixed in `b774c3e4`: `Supervisor::shutdown` now publishes the latch
     before it contends for the lock.
   - Regression test:
     `a_restart_queued_behind_a_launch_is_refused_once_shutdown_starts`. It
     counts launches through a file, so it proves that only the in-flight
     launch ran.
2. **Copilot: `LRH_CONSOLE_PYTHONPATH` skipped the absolute-path check.**
   - Fixed in `b774c3e4`: every `split_paths` entry must now be absolute.
   - Unit test added, and the docs table updated.
3. **Copilot: the primary execution record was missing.** It was already
   satisfied.
   - The bot reviewed `e119f63b`. The primary record
     `project/executions/WI-LRH-CONSOLE-DESKTOP-SHELL/2026_10_01_02_37_31_WI_LRH_CONSOLE_DESKTOP_SHELL.md`
     landed one commit later, in `1f9232ae`, with the smoke pass and the
     owner's impressions.
   - The `_SELFREVIEW` record's `pr:` field was linked in the same commit.

# Validation

- `cargo test --locked` passed three consecutive runs: 16 unit,
  7 capability-boundary, and 19 supervisor tests.
- `scripts/format --check --diff --desktop`, `scripts/lint --desktop`,
  `scripts/test --desktop`, `lrh validate`, and `scripts/check-workflows` all
  passed.

# Follow-up

Next is confirm-fixes: resolve the 3 threads, run a substitute cold review of
the new HEAD, and re-check CI.
