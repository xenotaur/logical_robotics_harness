---
execution_id: 2026_10_01_22_17_51_WI_LRH_CONSOLE_DESKTOP_SETTINGS_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_SETTINGS_SELFREVIEW)[2026-10-01T22:17:51+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
agent: "claude_app"
instruction_source: "project/work_items/proposed/WI-LRH-CONSOLE-DESKTOP-SETTINGS.md"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-10-01T22:17:51+00:00
---

# Summary

This record covers the pre-push `/lrh-self-review` of the
`WI-LRH-CONSOLE-DESKTOP-SETTINGS` branch at `dd675175`, run as `/lrh-implement`
Step 7.5. A cold-context general-purpose subagent reviewed the diff and only
reported findings. The invoking session applied the fixes it had verified.

# Result

The verdict was "needs fixes": no security holes, 0 blocking, 3 should-fix,
10 nits.

**Should-fix 1: ⌘Q skipped the non-blocking exit path.** I re-verified this
in the dependency source. muda 0.20 maps the predefined Quit to `terminate:`
(`macos/mod.rs:944`), and tao 0.37.1 only handles `applicationWillTerminate`,
so `RunEvent::Exit` runs without an `ExitRequested`. Fixed in `d52bd183`:

- A custom Quit item (⌘Q) calls `app.exit(0)`, which goes through
  `ExitRequested`. That path shows the Stopping page and stops off the main
  thread.
- `RunEvent::Exit` covers Dock and AppleScript quit. It now uses the new
  non-blocking `Supervisor::try_shutdown`, and the child stops itself on
  parent loss.

**Should-fix 2: `get_server_details` could freeze the UI.** It locked
`current` from the main thread during a Start. Fixed with
`Supervisor::try_diagnostics`.

**Should-fix 3: saving under the `LRH_CONSOLE_*` override defeated it.** When
the override is active, a save now writes only the file, and the UI explains
this.

**Nits fixed:**

- Loopback detection parses IP addresses: all of 127/8, 0.0.0.0, mapped IPv6,
  `localhost.`, and `*.localhost`.
- Menu handoffs and link handoffs use separate rate limiters.
- Downloads go to the browser through `on_download`. The Settings window
  denies them.
- 0600 permissions are enforced on the temp file.
- Only the first configuration auto-starts the backend.
- A duplicate Start keeps the current page.
- `restart_server` errors are handled in the UI.
- The docs now state the handoff and version-check limitations.

**Nits documented rather than changed:**

- A scripted or iframe navigation can trigger a handoff, still rate-limited.
- The protocol version is checked at handshake, not at save time.

# Validation

After the fixes:

- `cargo test --locked`: 26 unit, 9 capability, and 21 supervisor tests
  passed. That includes the new tests for unconfigured start and
  `try_shutdown`.
- `scripts/format --check --diff --desktop`, `scripts/lint --desktop`,
  `scripts/test --desktop`, `lrh validate`, and `scripts/check-workflows` all
  passed.

# Follow-up

None for this record. The real-window smoke pass is recorded in the primary
record.
