---
execution_id: 2026_10_01_02_36_33_WI_LRH_CONSOLE_DESKTOP_SHELL_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_SHELL_SELFREVIEW)[2026-10-01T02:36:33+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
agent: "claude_app"
instruction_source: "project/work_items/proposed/WI-LRH-CONSOLE-DESKTOP-SHELL.md"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-10-01T02:36:33+00:00
---

# Summary

This is the pre-push `/lrh-self-review` of the `WI-LRH-CONSOLE-DESKTOP-SHELL`
branch, run by `/lrh-implement` Step 7.5 at `c02b9657`. It ran in diff mode,
using a cold-context general-purpose subagent. The review only reported;
the invoking session applied the fixes it had verified.

# Result

The verdict was "ready to push after the two should-fix items". There were
no blocking findings, 2 should-fix, and 7 nits.

**Should-fix 1, Quit can relaunch.** I re-verified this one directly by
reading `shell.rs` and `lib.rs`.

- The bug: `ShellState::shutdown` called `supervisor.stop()`. The worker could
  then still dequeue a Start or Restart that had been queued before Quit, and
  spawn a new backend just before the process exited.
- The fix, in `af61f743`: `Supervisor::shutdown` sets a latch while holding
  the operation lock. Every later launch fails with `ErrorKind::ShutDown`.
- New test: `shutdown_stops_the_backend_and_refuses_later_launches`.

**Should-fix 2, panic on Exit after a failed setup.** The Exit handler
panicked when `ShellState` was never managed, which happens if setup failed.
It now uses `try_state`. This was also fixed in `af61f743`.

**Nits fixed in `af61f743`:**

- The crash poll interval is now 250 ms, and the interval is documented.
- `status.js` uses `Object.hasOwn`, so prototype names like `constructor` no
  longer resolve as states.
- Hide, Hide Others, and Show All are built only on macOS.
- The docs now say the close-hides-the-window behavior is macOS-only.

**Nits not changed:**

- *The capability tests exercise the policy directly.* No test proves that
  `build_main_window` wires `on_navigation` or `on_new_window`, because the
  mock runtime does not fire them. The real-window smoke test below covers
  that.
- *Serve content can navigate to bundled pages.* This is harmless today,
  since those pages have no commands. It is a note for SETTINGS, which adds
  bundled pages.
- *A Running state with an unparseable handshake URL.* `verify_ready`
  prevents this.

Re-verification also found a related problem in the developer launch settings,
fixed before review: canonicalizing the program path resolved a venv's
`python` symlink to the base interpreter.

# Validation

After the fixes:

- `cargo test --locked` passed: 16 unit, 7 capability-boundary, and 18
  supervisor tests.
- `scripts/format --check --diff --desktop`, `scripts/lint --desktop`,
  `scripts/test --desktop`, `lrh validate`, and `scripts/check-workflows` all
  passed.

# Follow-up

None for this record. The real-window smoke test and the owner's impressions
are in the primary record.
