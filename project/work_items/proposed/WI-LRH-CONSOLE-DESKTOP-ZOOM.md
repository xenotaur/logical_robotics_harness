---
id: "WI-LRH-CONSOLE-DESKTOP-ZOOM"
title: "Add Zoom In, Zoom Out, and Actual Size to the LRH Console window"
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
depends_on: []
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
- "The View menu has Zoom In (Cmd+=), Zoom Out (Cmd+-), and Actual Size (Cmd+0) items that change the main window's page zoom. (Owner decision at the plan gate: Cmd+= only, since the menu library allows one shortcut per item; Statusboard moves from Cmd+0 to Cmd+Shift+H.)"
- "The zoom level is global, survives navigation, Server > Restart, and quitting the app, and Actual Size resets it."
- "The current zoom level is visible somewhere unobtrusive (for example the window title or the menu) when it is not 100%."
required_evidence:
- "test_output"
- "manual_review"
- "lrh_validate"
artifacts_expected:
- "apps/desktop/src-tauri/src/shell.rs"
- "apps/desktop/src-tauri/src/settings.rs"
---

# Page zoom in LRH Console

## Summary

Add Claude- and Chrome-style page zoom to the LRH Console window, with menu items and the standard shortcuts, so large maps fit on a small screen.

## Problem / Context

The owner asked for zoom while reviewing the outline layout (PR #842): "it would really help seeing large projects when I don't have a large monitor", with Cmd+- and Cmd+= "plus appropriate menu items". The pinned Tauri (2.12.0) supports both a built-in zoom shortcut handler (`zoom_hotkeys_enabled`, which on macOS injects a script handling Cmd + - = +, 20% steps, 20% to 1000%) and setting the zoom from Rust (`set_zoom`, which needs the `core:webview:allow-set-webview-zoom` permission). The View menu is built in `apps/desktop/src-tauri/src/shell.rs`, next to Reload (Cmd+R), Back and Forward.

### Duplication search

In-repo: no zoom handling exists in `apps/desktop/`. Recommendation: proceed.

## Scope

- View > Zoom In, Zoom Out, and Actual Size, driven from Rust so the menu and shortcuts agree.
- A global zoom level saved with the app settings, like the window state from `WI-LRH-CONSOLE-DESKTOP-WINDOW-STATE`.
- A small cue showing the level when it is not 100%.

## Required Changes

1. Add the menu items and shortcuts, and apply zoom with `set_zoom`. Decide whether to also enable `zoom_hotkeys_enabled`, without producing two zoom steps per key press.
2. Save and restore the level.
3. Add tests for the menu wiring and the saved level, and check with the owner in a branch build.

## Non-Goals

- No per-page zoom.
- No zooming the dependency map independently of the page.

## Acceptance Criteria

- The View menu has Zoom In (Cmd+=), Zoom Out (Cmd+-), and Actual Size (Cmd+0) items that change the main window's page zoom. (Owner decision at the plan gate: Cmd+= only, since the menu library allows one shortcut per item; Statusboard moves from Cmd+0 to Cmd+Shift+H.)
- The zoom level is global, survives navigation, Server > Restart, and quitting the app, and Actual Size resets it.
- The current zoom level is visible somewhere unobtrusive (for example the window title or the menu) when it is not 100%.

## Validation

- `scripts/format --check --diff --desktop`
- `scripts/lint --desktop`
- `scripts/test --desktop`
- `lrh validate`
- Owner check in a branch build of LRH Console.

## Dependencies / Order

- None.

## Risk Notes

- Zoom changes the page's layout width, so the map's horizontal scrolling and the drawer overlay should be checked at 50% and 200%.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
