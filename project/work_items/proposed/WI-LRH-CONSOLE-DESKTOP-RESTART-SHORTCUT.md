---
id: "WI-LRH-CONSOLE-DESKTOP-RESTART-SHORTCUT"
title: "Add a Cmd+Shift+I shortcut to start or restart the LRH Console server"
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
