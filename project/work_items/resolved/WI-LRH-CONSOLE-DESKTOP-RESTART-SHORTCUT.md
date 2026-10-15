---
id: "WI-LRH-CONSOLE-DESKTOP-RESTART-SHORTCUT"
title: "Add a Cmd+Shift+I shortcut to start or restart the LRH Console server"
type: "deliverable"
status: "resolved"
blocked: false
blocked_reason: null
resolution: 'Implemented and merged in PR #845 (commit 3a233c6b). Cmd+Shift+I starts a stopped server at once and restarts a running one after a native confirmation sheet on the main window (''Restart the server? The current page will reload.'', Restart or Cancel). Start Server and Restart Server are one menu item, labelled by state, that always carries the shortcut, because muda 0.20 cannot clear a menu item''s key equivalent on macOS. Only one prompt can be open, a confirmed restart holds the guard until the worker claims it, and the stopped and failed pages mention the shortcut. The dialog comes from tauri-plugin-dialog 2.8.3, pinned and used from Rust only; tests check that its commands are denied in every window. The owner checked it on the branch app. A remaining narrow race between a Settings restart and a confirmed shortcut restart is tracked in WI-LRH-CONSOLE-RESTART-REQUEST-TOKEN.'
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
- "Server > Start or Restart Server is bound to Cmd+Shift+I: when the server is stopped it starts at once; when it is running it asks first."
- "The confirmation is a native dialog, 'Restart the server? The current page will reload.', with Restart and Cancel, and Cancel changes nothing."
- "The shortcut follows the server's state the way the Server menu does, and does nothing while a start or restart is already in progress."
required_evidence:
- "test_output"
- "manual_review"
- "lrh_validate"
artifacts_expected:
- "apps/desktop/src-tauri/src/shell.rs"
- "apps/desktop/src-tauri/Cargo.toml"
---

# Start or restart shortcut

## Summary

Give the server's start and restart a keyboard shortcut, Cmd+Shift+I, with a confirmation only when a running server would be restarted.

## Problem / Context

The owner restarts the server often while checking branch builds, and asked for a shortcut. Cmd+I already opens Server Details, so Cmd+Shift+I sits next to it. Today the Server menu's Start, Stop, and Restart Server items have no shortcuts (`apps/desktop/src-tauri/src/shell.rs`, `item(menu_id::RESTART, "Restart Server", false, None)`; the action is `Action::Restart`). Restarting reloads the page, so the owner asked for a confirmation "so users don't accidentally kill their view", and agreed that starting a stopped server needs none. Cmd+Shift+R was avoided because browsers use it for a hard reload.

### Duplication search

In-repo: no server shortcut exists. The app has no dialog dependency yet; a native confirmation likely needs the Tauri dialog plugin (`tauri-plugin-dialog`). Recommendation: proceed, and confirm that dependency when implementing.

## Scope

- One shortcut that starts or restarts, matching the server's state.
- A native confirmation before a restart.

## Required Changes

1. Bind Cmd+Shift+I to the Server menu's start or restart item, whichever applies.
2. Add the confirmation, choosing between the dialog plugin and an alternative, and say why in the PR.
3. Add tests for the state-dependent behavior, and check with the owner in a branch build.

## Non-Goals

- No shortcut for Stop Server.

## Acceptance Criteria

- Server > Start or Restart Server is bound to Cmd+Shift+I: when the server is stopped it starts at once; when it is running it asks first.
- The confirmation is a native dialog, 'Restart the server? The current page will reload.', with Restart and Cancel, and Cancel changes nothing.
- The shortcut follows the server's state the way the Server menu does, and does nothing while a start or restart is already in progress.

## Validation

- `scripts/format --check --diff --desktop`
- `scripts/lint --desktop`
- `scripts/test --desktop`
- `lrh validate`
- Owner check in a branch build of LRH Console.

## Dependencies / Order

- None.

## Risk Notes

- A new plugin dependency must be added to the app's capabilities with the narrowest permission that allows a confirmation.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
