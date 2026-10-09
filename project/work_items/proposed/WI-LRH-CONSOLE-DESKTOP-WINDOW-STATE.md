---
id: "WI-LRH-CONSOLE-DESKTOP-WINDOW-STATE"
title: "Larger default LRH Console window that remembers its size and placement"
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
- "WI-LRH-CONSOLE-DESKTOP-SETTINGS-POLISH"
blocked_by: []
expected_actions:
- "create_file"
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
- "On first launch, the main window is about 1.4 times today's 1100 by 760 size, limited to 90% of the current display."
- "The main window reopens at its last size and position, on the same display when it is still connected; a window that would be off-screen is moved fully onto a visible display."
- "Settings has a control that clears the saved size and position, and the next launch uses the default."
- "Saved window state lives with the app's settings, is never sent to the backend, and a corrupt saved state falls back to the default without an error dialog."
required_evidence:
- "test_output"
- "manual_review"
- "lrh_validate"
artifacts_expected:
- "apps/desktop/src-tauri/src/shell.rs"
- "apps/desktop/src-tauri/src/settings.rs"
- "apps/desktop/ui/ (Settings control)"
- "docs/how-to/lrh-console-local-dogfood.md"
---

# Window size and placement

## Summary

Open LRH Console's main window larger by default, and have it remember its size and position until the owner clears them in Settings.

## Problem / Context

While checking PR #805, the owner asked for the window to be 25% to 50% larger, as long as it fits the screen, and for it to remember its size and placement unless cleared in Settings. Today the main window always opens at 1100 by 760 (`apps/desktop/src-tauri/src/shell.rs`, `.inner_size(1100.0, 760.0)`), and nothing is remembered.

### Duplication search

In-repo: there is no window-state code. App settings persist through `apps/desktop/src-tauri/src/settings.rs`. Tauri's window-state plugin is an option, but it adds a dependency and writes its own file; prefer the existing settings store unless the plugin is clearly simpler. Recommendation: proceed.

## Scope

- The main window's default size, and saving and restoring its size and position.
- A Settings control that clears the saved state.

## Required Changes

- Compute the default size from the current display: about 1540 by 1064, clamped to 90% of the display's work area.
- Save the size, position, and display on move or resize (debounced) and on close, and restore them at launch, with an off-screen check.
- Add a Settings control that clears the saved state.
- Leave the Settings window's own size alone, unless that is trivial to include.

## Non-Goals

- No multi-window or tab layout.
- No remembering of the page or scroll position (separate from this).

## Acceptance Criteria

- On first launch, the main window is about 1.4 times today's 1100 by 760 size, limited to 90% of the current display.
- The main window reopens at its last size and position, on the same display when it is still connected; a window that would be off-screen is moved fully onto a visible display.
- Settings has a control that clears the saved size and position, and the next launch uses the default.
- Saved window state lives with the app's settings, is never sent to the backend, and a corrupt saved state falls back to the default without an error dialog.

## Validation

- `scripts/format --check --diff --desktop`
- `scripts/lint --desktop`
- `scripts/test --desktop`
- `lrh validate`
- The owner checks it in a branch build: resize, move, quit, relaunch, clear in Settings, and relaunch again.

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-DESKTOP-SETTINGS-POLISH` (resolved), which settled the Settings layout.

## Risk Notes

- Display arrangements change (a laptop is undocked). Always check that the restored frame is visible.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md`
