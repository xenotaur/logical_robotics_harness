---
id: "WI-LRH-CONSOLE-DESKTOP-BACK-NAV"
title: "Add a visible Back control to the LRH Console window"
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
- "WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH"
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
- "A visible Back control (and Forward, if the owner wants it) is available in the window without the keyboard or the menu bar, placed with the owner's agreement."
- "The control uses the existing app-side history from `WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH`, so it is enabled and disabled exactly when View > Back is."
- "The control works across served pages, keeps the loading cue behavior from `WI-LRH-CONSOLE-DESKTOP-LOADING-CUE`, and still works when page scripts are off."
required_evidence:
- "test_output"
- "manual_review"
- "lrh_validate"
artifacts_expected:
- "apps/desktop/src-tauri/src/shell.rs"
---

# Visible Back control in LRH Console

## Summary

Add an on-screen Back control to the LRH Console window, driven by the existing app-side history, so the user does not need the keyboard or the menu bar to go back.

## Problem / Context

In the L1 dogfood (`project/evidence/EV-LRH-CONSOLE-L1-DOGFOOD.md`, Run Two) the owner wrote: "A backbutton would be nice in addition to the backspace key." Back and Forward commands already exist: `WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH` (PR #771) added View > Back (Cmd+[) and View > Forward (Cmd+]) with an app-side history (`apps/desktop/src-tauri/src/shell.rs`, the `PageHistory` type and the View menu). They are enabled as pages are visited. The owner did not find them during the session, so what is missing is a visible control.

### Duplication search

In-repo: the menu commands and history exist (see above); no on-screen control does. Recommendation: proceed, reusing the existing history and menu routing.

## Scope

- A visible Back control, either in the served page frame or in the window, chosen with the owner.
- Optionally a Forward control, if the owner wants one.

## Required Changes

1. Add the control and route it to the existing Back command.
2. Keep its enabled state in step with View > Back.
3. Add tests for the wiring, and check with the owner in a branch build.

## Non-Goals

- No new history model, tabs, or multi-window history.
- No change to the existing menu items or shortcuts.

## Acceptance Criteria

- A visible Back control (and Forward, if the owner wants it) is available in the window without the keyboard or the menu bar, placed with the owner's agreement.
- The control uses the existing app-side history from `WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH`, so it is enabled and disabled exactly when View > Back is.
- The control works across served pages, keeps the loading cue behavior from `WI-LRH-CONSOLE-DESKTOP-LOADING-CUE`, and still works when page scripts are off.

## Validation

- `scripts/format --check --diff --desktop`
- `scripts/lint --desktop`
- `scripts/test --desktop`
- `lrh validate`
- Owner check in a branch build of LRH Console.

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH` (resolved).

## Risk Notes

- A control inside served pages must not appear when the same pages are opened in a browser, where the browser has its own Back.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/evidence/EV-LRH-CONSOLE-L1-DOGFOOD.md`
- `project/work_items/resolved/WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH.md`
