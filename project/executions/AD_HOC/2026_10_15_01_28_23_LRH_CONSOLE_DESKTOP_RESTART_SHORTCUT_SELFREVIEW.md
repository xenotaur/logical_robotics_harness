---
execution_id: 2026_10_15_01_28_23_LRH_CONSOLE_DESKTOP_RESTART_SHORTCUT_SELFREVIEW
prompt_id: PROMPT(AD_HOC:LRH_CONSOLE_DESKTOP_RESTART_SHORTCUT_SELFREVIEW)[2026-10-15T01:28:23+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_10_15_01_28_23_LRH_CONSOLE_DESKTOP_RESTART_SHORTCUT
pr: https://github.com/xenotaur/logical_robotics_harness/pull/845
commit:
created_at: 2026-10-15T01:28:23+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/845
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

This record covers a diff-mode `/lrh-self-review` of `WI-LRH-CONSOLE-DESKTOP-RESTART-SHORTCUT` (commit `ee3e12fc`), run before the PR's first push (PR #845). A cold-context `general-purpose` subagent did the review, report-only. It built a small native AppKit harness to test how menus handle key equivalents.

# Result

The implementing session re-verified the High finding in muda's source. The owner approved the fixes (option A, plus the Medium and Low fixes), and they landed in `c492dcd2`, without `--apply`.

1. **High:** muda 0.20.0's macOS `set_accelerator` ignores `None`, so a shortcut moved between Start and Restart stayed on both. The harness showed that a disabled first match swallows the key, so ⌘⇧I silently did nothing on a running server after any stop/start cycle. **Fix:** one Start/Restart item that always carries the shortcut, so it never moves.
2. **Medium:** the dialog had no parent. It showed as a free-floating system alert, could stack, and acted on stale state. **Fix:** a sheet on the main window, one prompt at a time, and a running-state check before restarting.
3. **Low:** the plugin's init script replaces the page's `alert` and `confirm`. **Fix:** a code comment, plus tests that the plugin's commands are denied in every window.
4. **Low:** the Settings capability was not pinned exactly, and one test inspected source text. **Fix:** the Settings permissions are pinned, and the test now checks the item's action and label per state.

The review confirmed several points:

- the shortcut string parses;
- the button mapping is right;
- the callback is thread-safe;
- `Cargo.lock` changed only by additions, plus the required `tauri-utils` patch bump;
- no capability grants `dialog:*` or `fs:*`.

# Validation

- `scripts/test --desktop` and `scripts/lint --desktop` pass after the fixes.
- The owner's seven-step check on the rebuilt app passed.

# Follow-up

- None. The PR still gets its first hosted bot review.
