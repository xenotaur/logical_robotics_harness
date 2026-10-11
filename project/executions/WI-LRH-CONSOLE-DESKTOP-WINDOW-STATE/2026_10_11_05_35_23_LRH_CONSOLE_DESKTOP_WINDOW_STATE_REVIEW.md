---
execution_id: 2026_10_11_05_35_23_LRH_CONSOLE_DESKTOP_WINDOW_STATE_REVIEW
prompt_id: PROMPT(WI-LRH-CONSOLE-DESKTOP-WINDOW-STATE:LRH_CONSOLE_DESKTOP_WINDOW_STATE_REVIEW)[2026-10-11T05:35:23+00:00]
work_item: WI-LRH-CONSOLE-DESKTOP-WINDOW-STATE
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/827
commit:
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/827"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-10-11T05:35:23+00:00
---

# Summary

This record covers review-response round 1 for PR #827 (`WI-LRH-CONSOLE-DESKTOP-WINDOW-STATE`), run as
part of `/lrh-land` inside `/lrh-execute`. It combines the owner's check of this branch's LRH Console
build with six bot threads, which raise five distinct issues.

- **CI** passed 7/7 on `03d679d7`.
- **The owner's check** (Mac app, branch build):
  1. The window opens larger, centered, and fully on screen.
  2. After a move and a quit, the relaunched window reopens in place. `window-state.json`
     recorded the move.
  3. Settings > Window > Reset returns the window to the default.
  4. After Reset, quit and relaunch: it opens at the default. `window-state.json` stayed absent,
     because the Reset hold worked.
  5. Multi-display was not checked: the owner was away from a multi-display setup. It is covered
     by unit tests only.
- **Friction:**
  - Step 2's first attempt used the Dock icon, which opens the installed
    `/Applications/LRH Console.app`, not the branch build. The owner retried with `open` on the
    branch bundle.
  - Opened that way, the build uses the saved configuration (`appearance: dark`,
    `start_on_open: false`, the `envs/LRH` `lrh`). Dark mode and a stopped server are expected
    from those settings. Developer launches ignore them.
  - A transient beach ball could not be reproduced. A 3 s sample showed the main thread idle.

# Result

All five issues were valid. The owner approved all five fixes, in
`1e6bfedb6e79703689d4b2e39a3e0c81c0c1bce0`:

- **Copilot and Codex, `settings.rs` (display identity):**
  - `SavedWindow` stores the display name and the frame's offset from its work area.
  - `place_window` returns the window to that display when one with that name is connected,
    wherever the display now sits in the arrangement. Otherwise it falls back to containment and
    then to overlap.
  - Older frame-only files still load.
  - Tests cover rearranging displays and the old format.
- **Copilot, `shell.rs` (saver race):** `WindowSaver::finish_if(seen)` checks for new moves and
  ends the saver in one locked step, so a move at that moment always waits its full delay. A test
  covers it.
- **Copilot, `shell.rs` (Reset errors):** every Reset step now returns its error to Settings.
- **Codex, `shell.rs` (Reset during full screen):**
  - `reset_window_state` is `#[tauri::command(async)]`.
  - It waits up to 3 s for full screen to finish exiting and holds all saving while it runs,
    because the restored pre-full-screen frame must not be saved.
  - It clears the file again after applying the default frame.
- **Codex, `lib.rs` (quit paths):** the frame is also saved on `RunEvent::Exit`, which covers Dock
  Quit, AppleScript, and logout.

# Validation

- `scripts/format --check --diff --desktop`, `scripts/lint --desktop`, and `scripts/test --desktop`
  pass (62 unit tests plus the integration and boundary suites).
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- Confirm-fixes with a substitute cold review, since hosted bots review only the first push.
