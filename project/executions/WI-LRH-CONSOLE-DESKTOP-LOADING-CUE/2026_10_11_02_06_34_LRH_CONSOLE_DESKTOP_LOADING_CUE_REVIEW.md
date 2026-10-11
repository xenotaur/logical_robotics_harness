---
execution_id: 2026_10_11_02_06_34_LRH_CONSOLE_DESKTOP_LOADING_CUE_REVIEW
prompt_id: PROMPT(WI-LRH-CONSOLE-DESKTOP-LOADING-CUE:LRH_CONSOLE_DESKTOP_LOADING_CUE_REVIEW)[2026-10-11T02:06:34+00:00]
work_item: WI-LRH-CONSOLE-DESKTOP-LOADING-CUE
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/821
commit:
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/821"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-10-11T02:06:34+00:00
---

# Summary

This record covers review-response round 1 for PR #821 (`WI-LRH-CONSOLE-DESKTOP-LOADING-CUE`), run as
part of `/lrh-land` inside `/lrh-execute`. It combines the owner's check of this branch's LRH Console
build with three bot threads.

- **CI** passed 7/7 on `e53dea51`.
- **The owner's check** (Mac app):
  1. Server > Restart takes about 1 to 2 s. During it, the window title reads "LRH Console —
     Loading…", then returns to "LRH Console".
  2. On restart, the page neither dims nor shows a loading pill. The app immediately shows its
     bundled "Starting server" page.
  3. The title cue appeared briefly on one slow page load.
  4. Warm pages are near instant, and the title does not flicker.
  5. Selecting a card on a dependency map does not change the title.
- **Diagnosis evidence** (for the acceptance criterion on the missing page-script pill):
  - On Restart and on the View menu, the app's shell navigates the window itself, either to its
    bundled status page or straight to a served page, so the page script never sees a click. The
    pill cannot fire there by design. The owner's step 2 confirms this for Restart.
  - The sidebar case could not be reproduced. With `WI-LRH-CONSOLE-CACHE-WARMUP` landed, served
    pages are near instant once warm, so no slow sidebar click was available to watch.
  - Code evidence rules out the shell re-issuing navigations: `on_navigation` returns `true` for
    backend pages.
  - Whether WebKit stops drawing the old page during a provisional load stays unconfirmed. The
    native title cue covers every path either way.

# Result

- **Copilot, `shell.rs` (the next navigation):** a cue already showing was not cleared when a new
  navigation started. An in-page jump after a slow load left "Loading…" up until the 20 s fallback.
  `LoadingCue::navigate` now ends any navigation in progress and resets the title before tracking
  the new one. A test covers it.
- **Copilot, execution record (owner check pending):** satisfied by the owner check and diagnosis
  recorded above.
- **Codex P2, `shell.rs` (fragment removal):** declined, with owner agreement, and replied on the
  thread. Under the HTML navigate algorithm, a navigation is same-document only when the new URL has
  a fragment. Going from `/meta#x` to `/meta` is a full load that reports `didFinishNavigation`, so
  the current check matches browser behavior. A test pins it.

Fix commit: `64d1715179aaced92183d0d6a5e3a4bf1fe79b62`.

# Validation

- `scripts/format --check --diff --desktop`, `scripts/lint --desktop`, and `scripts/test --desktop`
  pass (52 shell tests).
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- Confirm-fixes with a substitute cold review, since hosted bots review only the first push.
