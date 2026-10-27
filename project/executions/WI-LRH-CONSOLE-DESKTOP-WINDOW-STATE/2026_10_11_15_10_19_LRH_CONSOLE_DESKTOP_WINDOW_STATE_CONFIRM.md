---
execution_id: 2026_10_11_15_10_19_LRH_CONSOLE_DESKTOP_WINDOW_STATE_CONFIRM
prompt_id: PROMPT(WI-LRH-CONSOLE-DESKTOP-WINDOW-STATE:LRH_CONSOLE_DESKTOP_WINDOW_STATE_CONFIRM)[2026-10-11T15:10:19+00:00]
work_item: WI-LRH-CONSOLE-DESKTOP-WINDOW-STATE
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/827
commit: 4c55e0e69754b64fbc5ac413ff61095fe90c37a6
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/827"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-10-11T15:10:19+00:00
---

# Summary

This record covers confirm-fixes for PR #827 (`WI-LRH-CONSOLE-DESKTOP-WINDOW-STATE`), run as part of
`/lrh-land` inside `/lrh-execute`. Hosted review bots review only a PR's first push, so cold-context
substitute reviews stood in for them. The run stopped once and the owner restarted it.

# Result

- **First substitute review** (`03d679d7..f8905ead`):
  - Three threads were Clear-satisfied and resolved: the saver race, Reset errors, and the save
    on exit.
  - Two fixes failed on re-check, so the **stop-work condition fired** and the run stopped:
    - **Full-screen Reset (High):** the fix was a no-op. tao clears its full-screen state as soon
      as an exit is requested, so the wait never waited.
    - **Display identity (Medium-High):** it was keyed on the macOS model number, so identical
      monitors could swap the window. That was a regression.
  - The owner chose option A: amend the stop condition and continue in this PR.
- **Round 2 fixes** (`8a2e19a5`):
  - **Full screen:** Reset waits for the resizes from the exit to go quiet (400 ms, with a 4 s
    cap), and unzooms a zoomed window.
  - **Display matching:** the exact frame is restored first. The offset move happens only when
    exactly one display has the name.
  - **Saving and Reset:** a write lock spans the save check, the write, and Reset's clears. A
    second Reset is refused.
  - **Owner Mac check:** full screen, then Reset, ends at the default, and the next relaunch also
    opens at the default.
- **Second substitute review** (`f8905ead..8a2e19a5`):
  - All four fixes were Clear-satisfied, with no deadlocks.
  - The remaining three threads, for display identity and full screen, were resolved.
  - Three low findings were fixed at the owner's request in
    `5b9be8a54915dcc607266f91aac5c840c5d2f064`:
    - a stalled save is refused if anything happened since it read the frame;
    - the identical-display test was renamed to what it guarantees;
    - Settings disables Reset while one runs.
- **Owner checks:** steps 1 to 4 and full-screen Reset passed on the Mac. Multi-display placement
  is covered only by unit tests, because no second display was available.
- **CI:** 7/7 green on `f8905ead` and `8a2e19a5`. The final head is checked before the merge ask.

# Validation

- `scripts/format --check --diff --desktop`, `scripts/lint --desktop`, and `scripts/test --desktop`
  pass (65 unit tests plus the integration and boundary suites).
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- None for this PR.
- Multi-display placement awaits a hands-on check whenever the owner is at a multi-display setup.
