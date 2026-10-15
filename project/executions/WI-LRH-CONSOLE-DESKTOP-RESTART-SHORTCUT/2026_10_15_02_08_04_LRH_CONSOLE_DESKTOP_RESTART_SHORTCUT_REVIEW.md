---
execution_id: 2026_10_15_02_08_04_LRH_CONSOLE_DESKTOP_RESTART_SHORTCUT_REVIEW
prompt_id: PROMPT(WI-LRH-CONSOLE-DESKTOP-RESTART-SHORTCUT:LRH_CONSOLE_DESKTOP_RESTART_SHORTCUT_REVIEW)[2026-10-15T02:08:04+00:00]
work_item: WI-LRH-CONSOLE-DESKTOP-RESTART-SHORTCUT
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/845
commit:
created_at: 2026-10-15T02:08:04+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/845
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

This record covers review-response round 1 for PR #845 (`WI-LRH-CONSOLE-DESKTOP-RESTART-SHORTCUT`), run as part of `/lrh-land` inside `/lrh-execute`. CI passed 7/7 on the first push. Codex left one thread, and Copilot left none. The thread was valid, and the owner approved the fix.

# Result

- **Codex P2 (keep restart blocked until the queued action becomes busy):** valid.
  - **Problem:** accepting the dialog cleared the one-prompt guard before the restart was queued. The supervisor still reported Running, and the menu item stayed enabled until the worker took the request. A second ⌘⇧I in that window could open another prompt and queue a second restart.
  - **Fix:** a `RestartGuard` with three states: idle, asking and confirmed.
    - `begin` opens a prompt only when the guard is idle.
    - `answered` moves to confirmed when the restart is requested, and back to idle on Cancel or when the server is no longer running.
    - The worker calls `claimed` right after it marks the menu busy, and also when it drops the action at shutdown. `claimed` releases only a confirmed restart, so a restart from Settings while a prompt is open leaves that prompt the only one.
  - **Test:** a unit test covers the handoff.

# Validation

- `scripts/format --check --diff --desktop`: clean.
- `scripts/lint --desktop`: clean.
- `scripts/test --desktop`: Python 2360 OK; Rust 86, 13 and 23 tests passed.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- Confirm-fixes with a substitute cold review.
