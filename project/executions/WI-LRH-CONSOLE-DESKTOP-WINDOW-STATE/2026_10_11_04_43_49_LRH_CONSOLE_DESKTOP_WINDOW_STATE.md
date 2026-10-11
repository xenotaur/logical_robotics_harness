---
execution_id: 2026_10_11_04_43_49_LRH_CONSOLE_DESKTOP_WINDOW_STATE
prompt_id: PROMPT(WI-LRH-CONSOLE-DESKTOP-WINDOW-STATE:LRH_CONSOLE_DESKTOP_WINDOW_STATE)[2026-10-11T02:55:30+00:00]
work_item: WI-LRH-CONSOLE-DESKTOP-WINDOW-STATE
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/827
commit:
created_at: 2026-10-11T04:43:49+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/827
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

`/lrh-execute WI-LRH-CONSOLE-DESKTOP-WINDOW-STATE` ran on this item directly:

- it was available on `origin/main` as `proposed`;
- its dependency (SETTINGS-POLISH) was resolved;
- readiness was `prompt_ready: yes`;
- there was no prior record or overlapping PR.

The owner approved the plan, including a new Settings-only `reset_window_state` command.

# Result

- **Default size:** about 1540 x 1064 points, centered on the primary display. It is capped at
  90% of the work area, with a 400 x 300 floor.
- **Remembered placement:**
  - The content frame (inner position and size, in logical points) is saved to
    `window-state.json` beside the app's configuration.
  - It is saved once the window has been still for 500 ms after a move or resize, on close, and
    on quit. It is never saved while minimized or full screen.
  - At launch the frame is restored when it is fully on a connected display. Otherwise the window
    is moved, and shrunk if needed, onto a display.
  - A corrupt or implausible file falls back to the default.
- **Reset:** Settings > Window > Reset clears the file and applies the default at once. Saving
  stays held while the window sits on that frame, so the next launch uses the default.
- **Pre-push cold review:** 1 high, 1 medium, and 5 low findings, all fixed in `7351edee`:
  - **High:** outer versus inner origin made the window creep up by the title bar on each launch.
  - **Medium:** Reset re-saved its own frame.
  - **Low:**
    - a quit did not save;
    - each move or resize event spawned a thread;
    - overlapping saves shared a temp file;
    - a zero-size work area produced a zero-size window;
    - Reset ran while full screen or minimized.

# Validation

- `scripts/format --check --diff --desktop`, `scripts/lint --desktop`, and `scripts/test --desktop`
  pass (60 unit tests plus the integration and boundary suites).
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- An owner check in the branch build: resize, move, quit, relaunch, Reset in Settings, then
  relaunch again.
