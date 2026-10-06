---
execution_id: 2026_10_05_20_20_18_WI_LRH_CONSOLE_DESKTOP_SHELL_POLISH
prompt_id: PROMPT(WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH:WI_LRH_CONSOLE_DESKTOP_SHELL_POLISH)[2026-10-05T20:01:31+00:00]
work_item: WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/771
commit: 356615f8b5bafecfc4f014289e0e59ec0ce08446
agent: "claude_app"
instruction_source: "project/work_items/proposed/WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH.md"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-10-05T20:20:18+00:00
---

# Summary

This record covers implementing `WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH`
(dogfood defects D8 and D7) through `/lrh-execute
WS-LRH-CONSOLE-LOCAL-DOGFOOD`, with `/lrh-implement` inline. At the chain
gate the owner approved the run plan and chose an app-side history over the
webview's own `history.back()`.

# Result

**D8.** View > Back (⌘[) and View > Forward (⌘]) are backed by `PageHistory`
in `apps/desktop/src-tauri/src/shell.rs`.

- It records only pages on the running server's origin, without fragments.
- Any other navigation ends it, including the status page shown on start,
  restart, stop, and Quit, even when the port is reused.
- A navigation to the page just behind or ahead is taken as that move. This
  covers the webview's own Delete-key Back and rapid repeated moves.
- The menu items are enabled only when there is a page to go to.
  `handle_menu` re-checks `NavigationPolicy::allows` before navigating.
- No capability, eval, or IPC was added.

The documented trade-offs are:

- a link to the previous page acts as Back;
- subframes cannot be told apart;
- the webview's own Back can still show a status page on the first page.
  That behavior predates this change.

**D7.** User-facing text says "server" throughout. In the status pages:
"Starting/Stopping LRH server…", "The LRH server stopped unexpectedly", and
"Incompatible server". In Settings: the "Server program" legend and the
Details "Server" row. The how-to was updated as well. Internal identifiers
and historical evidence records are unchanged.

**Term choice, recorded for the visual-language style guide:** user-facing
text calls the process the app runs "the server" ("LRH server" in full).
"LRH Serve" names the product feature and the `lrh serve` command.

**Docs.** `docs/how-to/lrh-console-local-dogfood.md` gains a Back/Forward row
in Everyday use, and checklist step 5 now exercises Back and Forward.

**No divergence from the approved plan.** Changing the Settings legend and
the Details label was within the plan's "settings.html and settings.js only
if they use the old term".

# Validation

- `scripts/format --check --diff --desktop` passed.
- `scripts/lint --desktop` passed.
- `scripts/test --desktop --log`: `Ran 1909 tests`, OK. Rust: 35 unit, 9
  capability, and 22 supervisor tests passed.
- `lrh validate`: 0 errors, 0 warnings.
- `apps/desktop/scripts/run bundle` built the app.
- The owner's manual Mac check of Back and Forward is pending. It is
  recorded in the confirm-fixes record when done.
- Environment: pinned tools from the `LrhLocalAgent` env, with `PYTHONPATH`
  set to this worktree.

# Follow-up

- Optional: decide whether the main window's native Delete-key Back should
  be disabled, so it never shows a status page.
