---
execution_id: 2026_10_06_03_54_48_WI_LRH_CONSOLE_DESKTOP_SETTINGS_POLISH
prompt_id: PROMPT(WI-LRH-CONSOLE-DESKTOP-SETTINGS-POLISH:WI_LRH_CONSOLE_DESKTOP_SETTINGS_POLISH)[2026-10-06T03:40:50+00:00]
work_item: WI-LRH-CONSOLE-DESKTOP-SETTINGS-POLISH
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/776
commit: b1f97272a64bbd0872c7af1d6fd7c3530a4e8fe4
agent: "claude_app"
instruction_source: "project/work_items/proposed/WI-LRH-CONSOLE-DESKTOP-SETTINGS-POLISH.md"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-10-06T03:54:48+00:00
---

# Summary

This record covers implementing `WI-LRH-CONSOLE-DESKTOP-SETTINGS-POLISH`
(dogfood items D6, D1, D2, D3, D4, R3, and R4) through `/lrh-execute
WS-LRH-CONSOLE-LOCAL-DOGFOOD`, with `/lrh-implement` inline.

At the chain gate the owner:

- approved the run plan and the scroll-into-view design: an eval of a
  bundled-page function, rather than a reload to `#details`;
- asked that GitHub runner cancellations be retried once instead of
  stopping the run.

# Result

- **D6.** `SettingsSection` (`Settings` or `Details`) is chosen per menu
  item. `show_settings(app, section)` evals `section.show_script()` in an
  already-open window. A closed window gets an `initialization_script`
  setting `lrhInitialSection`.
  - `settings.js` defines `lrhShowSection`, which scrolls and adds a
    `.flash` highlight.
  - No capability changed.
- **D1.** `same_directory` resolves symlinks with canonicalize, and
  `ServerDetails.same_workspace` carries the result. The Served workspace row
  then says it is the same directory as the configured workspace.
- **D2.** Under the override, the saved message and the source note say the
  browser choice applies now; `save_settings` calls `set_browser` before the
  Environment early return. The program and workspace wait for a later
  session.
- **D3.** An invalid override's problem text now says that saving cannot fix
  it, and to correct or unset the `LRH_CONSOLE_*` variables and reopen the
  app.
- **R3 and R4.** The window is 1120×760, with a two-column grid that falls
  back to one column below 52rem. Spacing is tighter, empty field errors are
  hidden, and two wrapping labels are shorter. Save and Restart are
  `button.primary`.
  - Measured by rendering `settings.html` in Chrome at 1120×760: the worst
    case (override note, problem message, Python form, Restart button, and
    saved message) ends at 752px, and the normal case at 582px.
- **D4.** The dead `let _ = pid;` line was removed. The test now asserts
  `child_pid().is_some()`.
- **Docs.** The how-to covers the two-column window, the details focus, and
  the symlink note.

**No material divergence from the approved plan.** `style.css` was in the
expected file list.

# Validation

- `scripts/format --check --diff --desktop` passed.
- `scripts/lint --desktop` passed.
- `scripts/test --desktop --log`: `Ran 1909 tests`, OK. Rust: 42 unit, 9
  capability, and 22 supervisor tests passed.
- `lrh validate`: 0 errors, 0 warnings.
- `apps/desktop/scripts/run bundle` built the app.
- The owner's manual Mac check is pending. It will be recorded in the
  confirm or closeout record.
- Environment: pinned tools from the `LrhLocalAgent` env, with `PYTHONPATH`
  set to this worktree.

# Follow-up

- Optional: give `button.primary` an accent color, in the visual-language
  style guide.
