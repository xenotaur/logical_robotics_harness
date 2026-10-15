---
execution_id: 2026_10_15_02_25_40_LRH_CONSOLE_DESKTOP_RESTART_SHORTCUT_CLOSEOUT_NOTE
prompt_id: PROMPT(WI-LRH-CONSOLE-DESKTOP-RESTART-SHORTCUT:LRH_CONSOLE_DESKTOP_RESTART_SHORTCUT_CLOSEOUT_NOTE)[2026-10-15T02:25:40+00:00]
work_item: WI-LRH-CONSOLE-DESKTOP-RESTART-SHORTCUT
status: landed
rerun_of: 2026_10_15_01_28_23_LRH_CONSOLE_DESKTOP_RESTART_SHORTCUT
pr: https://github.com/xenotaur/logical_robotics_harness/pull/845
commit: 3a233c6b86553b663e95bc1156cb5ce4f063c790
created_at: 2026-10-15T02:25:40+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/845
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

This is the closeout note for PR #845, which implemented `WI-LRH-CONSOLE-DESKTOP-RESTART-SHORTCUT` through
`/lrh-execute RESTART-SHORTCUT`. The primary record's body is immutable, so the chain note lives here
instead.

# Result

CHAIN-NOTE: `cycles=1; stops=0; gates=[execute-chain-dialog-option-A, owner-check, prepush-fix-approval, owner-recheck, owner-page-text, land-chain, review-response, confirm-fixes, merge-and-followup]; friction=menu-library-cannot-clear-shortcut; self_review_rounds=2; bot_rounds=1; note="Cmd+Shift+I now starts a stopped server at once and restarts a running one after a confirmation sheet on the main window, which reads 'Restart the server? The current page will reload.' with Restart and Cancel. Start Server and Restart Server became one menu item that always carries the shortcut. The pre-push review proved, with a native AppKit harness, that muda 0.20 cannot clear a menu item's key equivalent on macOS, so moving the shortcut between two items left it stuck on the disabled one. The owner's first check had missed this because it never pressed the shortcut on a running server after a stop. The fix also attached the dialog to the window, allowed only one prompt at a time, pinned the Settings permissions, and checked that the dialog plugin's commands are denied everywhere. At the owner's suggestion, the stopped and failed pages mention the shortcut. Codex found that a second restart could slip through between confirming and the worker picking up the restart; a three-state guard now holds until the worker claims it. tauri-plugin-dialog 2.8.3 is pinned, with a required tauri-utils patch bump. CI passed 7/7, and the merge was SHA-locked."`

PR #845 merged as `3a233c6b86553b663e95bc1156cb5ce4f063c790`, using
`--match-head-commit a1f39643`, after authorization in this session. Four records landed with that
commit, through `lrh prompt update-execution`: the primary, `_REVIEW`, `_CONFIRM`, and the pre-push
`AD_HOC` `_SELFREVIEW`.

`WI-LRH-CONSOLE-DESKTOP-RESTART-SHORTCUT` moved to `resolved/` with a resolution note. At the owner's request,
`WI-LRH-CONSOLE-RESTART-REQUEST-TOKEN` was filed. `WS-LRH-CONSOLE-LOCAL-DOGFOOD` stays active.

# Validation

- `lrh validate` was run after these closeout edits. See the closeout commit.

# Follow-up

- `WI-LRH-CONSOLE-RESTART-REQUEST-TOKEN`: close the remaining race between a Settings restart and a confirmed shortcut restart.
