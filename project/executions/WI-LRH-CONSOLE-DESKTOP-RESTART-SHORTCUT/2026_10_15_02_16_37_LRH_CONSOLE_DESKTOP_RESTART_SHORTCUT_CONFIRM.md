---
execution_id: 2026_10_15_02_16_37_LRH_CONSOLE_DESKTOP_RESTART_SHORTCUT_CONFIRM
prompt_id: PROMPT(WI-LRH-CONSOLE-DESKTOP-RESTART-SHORTCUT:LRH_CONSOLE_DESKTOP_RESTART_SHORTCUT_CONFIRM)[2026-10-15T02:16:37+00:00]
work_item: WI-LRH-CONSOLE-DESKTOP-RESTART-SHORTCUT
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/845
commit: 3a233c6b86553b663e95bc1156cb5ce4f063c790
created_at: 2026-10-15T02:16:37+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/845
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

This record covers confirm-fixes for PR #845 (`WI-LRH-CONSOLE-DESKTOP-RESTART-SHORTCUT`), run as part of `/lrh-land` inside `/lrh-execute`. Hosted review bots review only a PR's first push, so a cold-context substitute review checked the review-round head, `175d2b53`.

# Result

- **The Codex P2 thread (a second restart slipping through) is Clear-satisfied.** The reviewer traced the timeline:
  - The dialog callback stores CONFIRMED before it requests the restart, so a press in between fails `begin()`.
  - The worker's `items.apply(MenuEnablement::BUSY)` runs synchronously on the main thread, through Tauri 2.12's `run_item_main_thread!`.
  - Only then does the worker call `claimed()`.

  So there is no interval with the item enabled, the guard idle and the restart pending. The reviewer also found no stuck-guard path: the shutdown branch releases the guard, and the only other early `continue` applies to Start. The thread is resolved.
- **Noted, not changed (Low):**
  - `claimed()` cannot tell which queued restart it is taking. If a Settings restart races a confirmed shortcut restart, the guard can be released one restart early, and a third press in a sub-poll window could then queue a third restart. This needs two restart sources racing plus a third press, so it was left as a possible follow-up; a per-request token would close it.
  - The worker wiring is untested. The state machine is unit-tested, and the owner's checks covered the behaviour.
- **CI:** 7/7 green on `175d2b53`.
- **Owner checks:** all seven steps passed on the rebuilt branch app. The guard fix only narrows a sub-poll timing window, which cannot be checked by hand.

# Validation

- `scripts/test --desktop`: 86, 13 and 23 Rust tests passed (the reviewer's own run).
- `scripts/lint --desktop`: clean.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- File `WI-LRH-CONSOLE-RESTART-REQUEST-TOKEN` only if the owner wants the Low race closed; otherwise none.
