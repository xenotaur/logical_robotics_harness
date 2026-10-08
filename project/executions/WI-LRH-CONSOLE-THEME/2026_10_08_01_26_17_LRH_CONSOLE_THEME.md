---
execution_id: 2026_10_08_01_26_17_LRH_CONSOLE_THEME
prompt_id: PROMPT(WI-LRH-CONSOLE-THEME:LRH_CONSOLE_THEME)[2026-10-08T01:08:11+00:00]
work_item: WI-LRH-CONSOLE-THEME
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/786
commit: 06fbcc7a4e7e7a65ea8af7c0e41039bfd7744152
agent: "claude_app"
instruction_source: "user request in session: /lrh-execute WS-LRH-CONSOLE-LOCAL-DOGFOOD (chain approved: \"Approve as stated\")"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-10-08T01:26:17+00:00
---


# Summary

This record covers the implementation of `WI-LRH-CONSOLE-THEME` through `/lrh-execute`: Serve
pages follow the system theme by default, `lrh serve --theme` pins one, and LRH Console adds an
Appearance setting. The owner approved the chain and run plan in this session ("Approve as
stated").

# Result

- **`src/lrh/serve.py`:**
  - The `data-theme="light"` attribute is removed from all 11 template roots.
  - New: `THEMES`, `DEFAULT_THEME`, `ServeConfig.theme`, and `apply_theme`, which pins the first
    `<html lang="en">` in every `text/html` write.
  - `--theme {light,dark,system}` is added; it is allowed with `--desktop-protocol`, and
    `_desktop_server_factory(..., theme=)` passes it on.
  - `status_payload` gains `theme`, and the `/style` copy and protocol help are updated.
- **Desktop:**
  - `settings.rs` adds `Appearance` (with `#[serde(default)]` System). `launch_config` always
    passes `--theme`, and `needs_restart` includes appearance.
  - `supervisor.rs` adds `LaunchConfig.serve_args`, appended after `serve --desktop-protocol`.
  - `shell.rs` applies the appearance with `AppHandle::set_theme` at startup and on save;
    `save_settings` is now generic over the runtime.
  - Settings gets a three-way Appearance radio group, with updated messages.
- **Tests:**
  - `serve_test.py` covers the flag, the default, invalid values, `--show-config`,
    `--desktop-protocol` acceptance, `apply_theme`, the default and pinned themes across six
    HTML routes, and the desktop factory.
  - `tokens_test.py` checks that every template root is unpinned.
  - `settings.rs` unit tests cover an older file without `appearance`, the launch arguments, and
    `needs_restart`. `shell.rs` covers the native-theme mapping.
  - `supervisor_test.rs` adds `serve_args_reach_the_backend`, which runs a real backend with
    `--theme dark`.
  - The smoke monkeypatch now forwards options.
- **Docs:** the `lrh serve` reference, the desktop server protocol, and the dogfood how-to.

**Pre-push cold review.** Verdict: safe to push, with no must-fix items. It confirmed that every
HTML path goes through `_write_text`, that the replace cannot misfire, that `set_theme` is
sound on Tauri 2.12/macOS with an unchanged capability boundary, and that the docs are
accurate. Applied in `99b677b2`: two more routes in the pinning test, a comment re-wrap, and the
environment-override wording.

One gap is noted in the PR: under `LRH_CONSOLE_*`, the saved appearance applies to app windows
only after a save, the same as the browser choice.

# Validation

- `scripts/format --check --diff --desktop`, `scripts/lint --desktop`, and
  `scripts/test --desktop` pass: 1976 Python tests, and desktop tests 44, 9 and 23.
- `tests/smoke/desktop_protocol_smoke.py` passes (21 tests).
- `lrh validate`: 0 errors, 0 warnings.
- Browser pane: the default follows dark emulation on `/` and `/meta`, and `--theme light` stays
  light under dark emulation.

# Follow-up

- The owner checks the app on a Mac: Settings > Appearance (Light, Dark, System) and Restart
  server now.
- `WI-LRH-CONSOLE-INTERACTIVE`: the in-page switch must detect a pinned theme (for example the
  `theme` in `/api/status`) rather than overwrite it.
