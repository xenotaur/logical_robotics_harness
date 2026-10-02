---
execution_id: 2026_10_01_22_19_40_WI_LRH_CONSOLE_DESKTOP_SETTINGS
prompt_id: PROMPT(WI-LRH-CONSOLE-DESKTOP-SETTINGS:WI_LRH_CONSOLE_DESKTOP_SETTINGS)[2026-10-01T18:22:28+00:00]
work_item: WI-LRH-CONSOLE-DESKTOP-SETTINGS
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/763
commit: abe0acf6bf9d67949927f6f1147526737daa5561
agent: "claude_app"
instruction_source: "project/work_items/proposed/WI-LRH-CONSOLE-DESKTOP-SETTINGS.md"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-10-01T22:19:40+00:00
---

# Summary

Implementation of `WI-LRH-CONSOLE-DESKTOP-SETTINGS`. The user ran
`/lrh-execute WS-LRH-CONSOLE-LOCAL-DOGFOOD`, which resolved to this item because
SHELL was resolved and DOGFOOD depends on this one. The run used
`/lrh-implement` inline, and `/lrh-land` follows. The branch
`xenotaur/feat/wi-lrh-console-desktop-settings` was cut from `origin/main` at
`edb9986d`.

At the run gate, the owner approved these additions to the plan:

- `apps/desktop/scripts/run bundle` and `launch`;
- View > Meta, from the SHELL smoke feedback;
- the Quit stall fix deferred from SHELL;
- a rule that only clicks on `http(s)` links are handed off, at most one per
  second.

The run used the stored default chain conditions.

# Result

The main implementation is `dd675175`.

- **Configuration** (`src/settings.rs`): a private, validated configuration
  with an atomic 0600 store. An invalid save keeps the last working values,
  and launch changes take effect only on restart.
- **Supervisor**: can start unconfigured, and `set_config` applies at the next
  launch.
- **First run**: if no configuration exists, the app opens Settings.
- **Settings / Server Details window**: one window that shows bundled pages
  only and is the only one granted the narrow commands
  (`capabilities/settings-window.json`).
- **Recovery pages**: setup, failed with per-code actions, and incompatible.
- **Browser handoff** (`src/browser.rs`): http(s) only, through `/usr/bin/open`,
  with a Chrome-to-default fallback and rate limiting.
- **New menu items**: View > Meta, Open in Chrome, and Open in Default Browser.
- **Quit**: the backend is stopped off the main thread.
- **Scripts**: `run bundle` and `run launch`, with tests.
- **Docs**: `docs/how-to/lrh-console-local-dogfood.md`, which includes the
  15-step checklist, plus toolchain doc updates.

`d52bd183` applies the pre-push self-review fixes:

- a custom ⌘Q, because the predefined item's `terminate:` skipped
  ExitRequested;
- non-blocking server details and `try_shutdown`;
- saves made while the environment override is active write only the file;
- IP-parsed loopback detection;
- separate rate limiters for links and menu items;
- downloads go to the browser;
- 0600 enforced on the temp file;
- only the first configuration starts the backend automatically.

The `_SELFREVIEW` record is `2026_10_01_22_17_51`.

# Validation

- `scripts/format --check --diff --desktop`: pass.
- `scripts/lint --desktop`: pass.
- `scripts/test --desktop`: pass. That covers the Python suite plus Rust tests:
  26 unit, 9 capability-boundary, and 21 supervisor.
- `scripts/test`: Rust-free, and prints the SKIPPED line.
- `lrh validate`: pass.
- `scripts/check-workflows`: pass.
- **Scripted Mac smoke**: `run bundle` built `LRH Console.app`. After `run
  launch`, the backend answered `/health` with 200. A scripted quit exited in
  0.7 s with no backend left.
- **Owner hand smoke** on build `d52bd183`, a true first run opened like
  Finder with no configuration:
  1. Settings opened by itself.
  2. A `/tmp` workspace was rejected with a field error, and nothing was
     saved.
  3. The real save started the server, and the dashboard appeared.
  4. Server Details showed the expected fields.
  5. Settings stayed a single window across ⌘, and ⌘I. Closing it kept the
     server running.
  6. View > Meta and View > Dashboard worked.
  7. Open in Chrome and Open in Default Browser worked.
  8. Not tested: no external links were present on the pages visited.
  9. The download was handed to the browser as expected. The prompt content
     itself was not useful, because almost every work item viewed was not
     prompt-ready.
  10. Restart-required appeared on a workspace change.
  11. ⌘Q quit cleanly.
  12. Skipped: reopen from saved settings, already exercised earlier.

  Afterwards no app or backend process remained. The configuration file was
  written with mode `0600`.

# Follow-up

- External-link handoff was not exercised by hand because Serve pages contain
  no external links. Unit tests cover it, and the DOGFOOD checklist step 6
  covers it if such links appear.
- Owner observation: most work items Serve showed were not prompt-ready, so
  the workbench prompt download was not illuminating. This concerns
  planning-data quality, not the app. It is input for the DOGFOOD sessions
  and for L1 dependency planning.
- Deferred: a version check before saving. The protocol version is checked at
  handshake time, and the docs now say so.
