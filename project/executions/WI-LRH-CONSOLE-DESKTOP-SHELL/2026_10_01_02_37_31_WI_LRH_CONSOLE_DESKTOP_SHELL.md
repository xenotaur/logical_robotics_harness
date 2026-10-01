---
execution_id: 2026_10_01_02_37_31_WI_LRH_CONSOLE_DESKTOP_SHELL
prompt_id: PROMPT(WI-LRH-CONSOLE-DESKTOP-SHELL:WI_LRH_CONSOLE_DESKTOP_SHELL)[2026-10-01T02:01:17+00:00]
work_item: WI-LRH-CONSOLE-DESKTOP-SHELL
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/762
commit: 3fed7dac2f5b3d82f487d3b8e86b96b10d4dd8b8
agent: "claude_app"
instruction_source: "project/work_items/proposed/WI-LRH-CONSOLE-DESKTOP-SHELL.md"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-10-01T02:37:31+00:00
---

# Summary

Implementation of `WI-LRH-CONSOLE-DESKTOP-SHELL`, run through a
human-initiated `/lrh-execute WS-LRH-CONSOLE-LOCAL-DOGFOOD`. That run resolved
to this item, the first ready item after SUPERVISOR. The work used
`/lrh-implement` inline, and `/lrh-land` follows.

- An earlier execute run resolved to SHELL but stopped before its gate, so
  that SHELL could first be split at the configuration/recovery boundary
  (PR #760).
- The branch `xenotaur/feat/wi-lrh-console-desktop-shell` was cut from
  `origin/main` at `335adca0`.
- At the run gate, the owner approved adding the app icon to this item: the
  LRH Icon v7 artwork, plus turning on macOS bundling.
- The gate also approved the stored default conditions:
  - Completion: PR merged, its execution records landed, and the work item
    resolved.
  - Stop-work: any failing CI check, a reviewer finding that isn't
    Clear-satisfied on re-verification, or an ambiguous or refused
    merge-authorization reply.

# Result

**`c02b9657`** delivered the shell itself.

- **`src/shell.rs`:**
  - The app-built main window shows a bundled status page, or, while the
    owned backend runs, that backend's verified origin.
  - `NavigationPolicy` allows only bundled pages and the current backend's
    exact origin. The origin is cleared before Stop and Restart.
  - Popups are denied.
  - Native Server, View, and Window menus are enabled according to state.
  - One worker thread runs every lifecycle action, so actions are
    serialized and run off the UI thread. The same thread polls for
    crashes.
  - The developer-only launch settings are read here.
- **`lib.rs`:** macOS close hides the window, Dock reopen shows it again, and
  Exit shuts the app down.
- **`capabilities/main-window.json`:** has no permissions.
- **`tests/capability_boundaries_test.rs`:** new tests.
- **Icons:** generated from `icons/source/lrh-icon-1024.png`, which was
  rendered from the owner's `.ai` file; bundling is now on.
- **Deferred PR #750 test nits:** included.
- **Docs:** updated.

**`af61f743`** applied the self-review fixes:

- a shutdown latch, so a Start or Restart queued before Quit cannot relaunch
  the backend;
- `try_state` on Exit;
- the remaining nits.

The `_SELFREVIEW` record is `2026_10_01_02_36_33`.

**Fixed before review:** canonicalizing the configured Python path resolved a
virtualenv to its base interpreter, so the shell now uses the path as given.

# Validation

- **Script checks:**
  - `scripts/format --check --diff --desktop`: pass.
  - `scripts/lint --desktop` (clippy `-D warnings`): pass.
  - `scripts/test --desktop`: pass, with 1904 Python tests, and Rust 16 unit,
    7 capability-boundary, and 18 supervisor tests.
  - `scripts/test`: Rust-free, and prints the desktop SKIPPED line.
  - `lrh validate`: pass.
  - `scripts/check-workflows`: pass.
- **Mac smoke, scripted:**
  - `cargo tauri build --bundles app` produced an 8.44 MiB `LRH Console.app`.
  - Launched with the developer settings, the app owned an `lrh serve`,
    which answered `/health` with 200.
  - An AppleScript `quit` left no app or backend process.
- **Mac smoke, by the owner, on build `af61f743`:** all 8 steps passed.
  1. Startup shows the dashboard.
  2. Stop shows the stopped page, and the menu enablement is correct.
  3. Start works.
  4. Restart works.
  5. In-app links work, and external links are refused.
  6. Closing the window hides it while the app keeps running.
  7. Clicking the Dock icon reopens it.
  8. ⌘Q quits.

  Afterwards no app or backend process remained, and the port was closed.

  The optional Restart-then-⌘Q race was not run by hand. The supervisor test
  `shutdown_stops_the_backend_and_refuses_later_launches` covers it.

# Follow-up

Owner impressions from the smoke pass, kept as input for later work:

- **Page loads were sometimes a bit slow.** This needs profiling: Serve
  rendering versus the webview. It is input for `WI-LRH-CONSOLE-DESKTOP-DOGFOOD`
  and L2.
- **The icon needs improvement.** That is already tracked elsewhere.
- **The UX doesn't look like the dependency-viewer mockups that started the
  work.** This is expected: L0 embeds the existing Serve dashboard, and the
  dependency map is L1. The mockups are in PR #737.
- **The dashboard page is long and completionist.** That helps debugging but
  hurts visibility. It is input for L1 and the console visual-language
  proposal.
- **There is no visible link to the Meta view from the dashboard.** Serve
  links back to Meta only from Meta subpages. Two candidate fixes: a small
  Serve change that adds a Meta link to the dashboard, or a View > Meta menu
  item in `WI-LRH-CONSOLE-DESKTOP-SETTINGS`.
