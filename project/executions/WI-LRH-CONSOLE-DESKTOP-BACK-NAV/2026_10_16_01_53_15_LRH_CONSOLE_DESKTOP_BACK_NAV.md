---
execution_id: 2026_10_16_01_53_15_LRH_CONSOLE_DESKTOP_BACK_NAV
prompt_id: PROMPT(WI-LRH-CONSOLE-DESKTOP-BACK-NAV:LRH_CONSOLE_DESKTOP_BACK_NAV)[2026-10-15T06:03:57+00:00]
work_item: WI-LRH-CONSOLE-DESKTOP-BACK-NAV
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/847
commit:
created_at: 2026-10-16T01:53:15+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/847
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

This record covers the implementation of `WI-LRH-CONSOLE-DESKTOP-BACK-NAV` under `/lrh-execute`, with the run plan approved by the owner. The owner placed both buttons right after the sidebar toggle, and approved the proposed design: buttons rendered by Serve but shown only inside LRH Console, and answered by the app's own history.

# Result

- **`frame.py`:**
  - Back and Forward links (`/desktop/back`, `/desktop/forward`) with Lucide `chevron-left` and `chevron-right` icons and the tooltips "Back (⌘[)" and "Forward (⌘])".
  - Hidden unless the root element has `lrh-in-app`.
  - They render greyed out (`aria-disabled="true"`, `tabindex="-1"`).
  - The gear and both buttons are marked `data-lrh-app-link`.
- **`shell.rs`:**
  - `IN_APP_SCRIPT` runs as the main window's `initialization_script`.
  - `NavigationPolicy::history_request` recognizes the two paths, on the backend origin only.
  - `on_navigation` intercepts them and runs `handle_menu(BACK/FORWARD)`.
  - `on_page_load` Finished evaluates `history_buttons_script(can_go_back, can_go_forward)`.
- **`lrh-interactive.js`:** the loading overlay skips greyed-out links, and app-answered links inside LRH Console. This fixes a pre-existing stuck "Loading…" dim after the gear opened Settings.
- **Docs:** the dogfood how-to.
- **Owner check on the branch build:** all 10 steps passed. They covered:
  - state cycling (‹ ‹ › ›, mixed menu, shortcut and button input, rapid double-click);
  - restart, stop and start;
  - the gear overlay;
  - tooltips;
  - absence in Chrome;
  - light and dark.

  The owner judged the grey-to-enabled flicker on load fine.
- **Pre-push self-review:** two findings, fixed in `a0480b4f`. See the `AD_HOC` `_SELFREVIEW` record.

# Validation

- `scripts/format --desktop`, `scripts/lint --desktop`: clean.
- `scripts/test --desktop`: Python 2362 OK; Rust 91, 14 and 23 tests passed.

# Follow-up

- Land through `/lrh-land`.
