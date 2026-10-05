---
id: "WI-LRH-CONSOLE-DESKTOP-SETTINGS-POLISH"
title: "Fix LRH Console Settings / Server Details defects and size the window to fit"
type: "deliverable"
status: "proposed"
blocked: false
blocked_reason: null
resolution: null
owner: "anthony"
contributors:
- "anthony"
assigned_agents: []
parent_id: "WS-LRH-CONSOLE-LOCAL-DOGFOOD"
related_focus: []
related_roadmap: []
related_workstreams:
- "WS-LRH-CONSOLE-LOCAL-DOGFOOD"
related_design:
- "project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md"
depends_on:
- "WI-LRH-CONSOLE-DESKTOP-DOGFOOD"
blocked_by: []
expected_actions:
- "edit_file"
- "run_tests"
- "create_pr"
forbidden_actions:
- "force_push"
- "delete_branch"
- "merge_pr"
- "publish_package"
- "deploy_remote_service"
acceptance:
- "Choosing Server > Server Details… (⌘I) scrolls to and highlights the Server Details section, whether or not the window was already open. Choosing Settings… (⌘,) shows the top."
- "When the configured and served workspace paths resolve to the same directory (for example via a symlink), Server Details says so instead of looking like a mismatch."
- "Under an active LRH_CONSOLE_* override, Settings text accurately says which saved changes apply now (the browser choice) and which wait. An invalid override tells the user to unset the LRH_CONSOLE_* variables, because saving cannot fix it."
- "The Settings window opens large enough to show every field and the Save and Restart buttons without scrolling on a 1440×900 display, and Save and Restart are larger primary buttons."
- "The dead `let _ = pid;` line in try_shutdown_never_waits_for_an_in_flight_launch is removed."
- "Tests cover the details-focus behavior and the workspace comparison. Format, lint, and desktop tests pass."
required_evidence:
- "test_output"
- "manual_review"
- "lrh_validate"
artifacts_expected:
- "apps/desktop/src-tauri/src/shell.rs"
- "apps/desktop/ui/settings.js"
- "apps/desktop/ui/settings.html"
- "apps/desktop/src-tauri/tests/supervisor_test.rs"
---

# LRH Console Settings polish

## Summary

Fix the Settings / Server Details defects from the L0 dogfood sessions and
the PR #763 final review, and size the window to fit its content.

## Problem / Context

These were found during `WI-LRH-CONSOLE-DESKTOP-DOGFOOD` and are recorded in
`project/evidence/EV-LRH-CONSOLE-DESKTOP-L0-DOGFOOD.md`:

- **D6 (session 2): Server Details does not scroll.** Choosing Server
  Details while Settings is open does not scroll to the details section, "so
  it isn't clear anything happened". Both menu items call the same function
  (`apps/desktop/src-tauri/src/shell.rs`, `handle_menu`:
  `menu_id::SETTINGS | menu_id::DETAILS => show_settings(app)`).
- **D1 (every session): symlinked workspace looks like a mismatch.**
  Configured workspace `/Users/centaur/Workspace/…/logical_robotics_harness`
  is a symlink to the served workspace
  `/Users/centaur/Tempspace/Projects/…/logical_robotics_harness`. Details
  shows both rows (`apps/desktop/ui/settings.js:90-91`) without saying they
  are the same directory.
- **D2 and D3 (PR #763 final cold review): override wording.**
  - Under the developer `LRH_CONSOLE_*` override, a browser-choice change
    applies at once, but the saved message says the session keeps using the
    override (`settings.js:119-120`).
  - With an invalid override, the page should tell the user to unset the
    variables.
- **D4 (PR #763 final cold review): dead test line.** There is a dead
  `let _ = pid;` at `apps/desktop/src-tauri/tests/supervisor_test.rs:356`.
- **R3 and R4 (session 0): window and button size.** The owner asked for
  larger Save and Restart buttons, and a default window that shows
  everything at once. The window opens at 720×760 (`build_settings_window`).

### Duplication search

- In-repo: these were recorded only as follow-ups in the
  `WI-LRH-CONSOLE-DESKTOP-SETTINGS` closeout note and the dogfood evidence.
  There is no existing work item.
- Recommendation: proceed.

## Scope

- Scroll Server Details into view, compare workspaces, fix the override
  wording, size the window and buttons, and remove the dead line.

## Required Changes

1. Distinguish the two menu actions. Server Details brings the window
   forward and scrolls to and highlights the details section, for example
   through an event or URL fragment the bundled page handles. Settings shows
   the top. Do not add any capability to the main window.
2. Have the Rust `get_server_details` command report whether the configured
   and served workspaces canonicalize to the same path. Python Serve does not
   know the configured path, so the comparison belongs in the shell. Show "same directory (via
   symlink)" when they do.
3. Fix the override wording for the browser-choice case and the
   invalid-override case.
4. Enlarge the default Settings window so every field and both buttons fit
   on a 1440×900 display, and make Save and Restart larger primary buttons.
5. Remove the dead `let _ = pid;` line.
6. Add tests for the details-focus path and the workspace comparison.

## Non-Goals

- No file-picker dialogs (R5). That needs Tauri's dialog plugin, a new
  native capability, and is a separate scope and security decision.
- No visual-language header, sidebar, or style guide work.

## Acceptance Criteria

- Server Details visibly scrolls into view.
- A symlinked workspace is shown as the same directory.
- The override text is accurate in both cases.
- The window fits its content, and the buttons are larger.
- The dead line is gone, and the tests cover the change.

## Validation

- `scripts/format --check --diff --desktop`
- `scripts/lint --desktop`
- `scripts/test --desktop`
- `lrh validate`
- A manual Mac check: with Settings open, choose ⌘I and confirm the scroll.
  Then confirm the symlinked workspace row.

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-DESKTOP-DOGFOOD`, whose evidence documents
  these defects.
- Independent of `WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH`.

## Risk Notes

- Canonicalizing paths can fail if the configured path disappears. Treat a
  failure as "not the same" and show both paths as today.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/evidence/EV-LRH-CONSOLE-DESKTOP-L0-DOGFOOD.md`
- `project/executions/WI-LRH-CONSOLE-DESKTOP-SETTINGS/2026_10_02_01_41_07_WI_LRH_CONSOLE_DESKTOP_SETTINGS_CLOSEOUT_NOTE.md`
