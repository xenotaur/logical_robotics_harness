---
execution_id: 2026_10_15_01_28_23_LRH_CONSOLE_DESKTOP_RESTART_SHORTCUT
prompt_id: PROMPT(WI-LRH-CONSOLE-DESKTOP-RESTART-SHORTCUT:LRH_CONSOLE_DESKTOP_RESTART_SHORTCUT)[2026-10-15T00:19:28+00:00]
work_item: WI-LRH-CONSOLE-DESKTOP-RESTART-SHORTCUT
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/845
commit: 3a233c6b86553b663e95bc1156cb5ce4f063c790
created_at: 2026-10-15T01:28:23+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/845
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

This record covers the implementation of `WI-LRH-CONSOLE-DESKTOP-RESTART-SHORTCUT` under `/lrh-execute`, with the run plan approved by the owner, including dialog option A (`tauri-plugin-dialog`). ⌘⇧I starts a stopped server at once and restarts a running one after confirmation.

# Result

- **`shell.rs`:**
  - One Server menu item, `menu_id::START_OR_RESTART`, labelled Start Server or Restart Server by state and always carrying `SERVER_SHORTCUT`. It replaces the separate Start and Restart items.
  - `server_item_action` and `server_item_label` derive the item's behavior from `MenuEnablement`.
  - `confirm_restart` shows a sheet on the main window, allows only one open at a time (`ShellState.confirming`), and restarts only if the server is still running.
- **`lib.rs`:** registers `tauri_plugin_dialog`, with a comment about its `alert`/`confirm` replacement.
- **`Cargo.toml` and `Cargo.lock`:** `tauri-plugin-dialog = "=2.8.3"`. This adds packages and bumps `tauri-utils` to 2.10.1, as `tauri-plugin` 2.7.1 requires.
- **`status.js`:** the stopped and failed pages mention ⌘⇧I, at the owner's suggestion during the check.
- **Capability tests:** the Settings permissions are pinned exactly, and the dialog commands are denied in every window.
- **Docs:** the dogfood how-to describes the shortcut.
- **Owner checks on branch builds:**
  - **First build** (`ee3e12fc`): the owner's steps 1 to 6 passed. That sequence never pressed ⌘⇧I on a running server after a stop/start cycle, which is the case the pre-push review then found broken.
  - **Rebuilt build** (`c492dcd2`): all seven steps passed, including that case, the attached sheet, and only one prompt on a double press.
- **Pre-push self-review:** 1 High, 1 Medium and 2 Low findings, all fixed in `c492dcd2`. See the `AD_HOC` `_SELFREVIEW` record.

# Validation

- `scripts/format --check --diff --desktop`: clean.
- `scripts/lint --desktop`: clean.
- `scripts/test --desktop`: Python 2360 OK; Rust 85, 13 and 23 tests passed.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- Land through `/lrh-land`.
- The owner may glance at the new ⌘⇧I text on the stopped page in the rebuilt app.
