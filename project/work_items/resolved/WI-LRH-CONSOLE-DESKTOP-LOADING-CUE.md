---
id: "WI-LRH-CONSOLE-DESKTOP-LOADING-CUE"
title: "Show a native loading cue in LRH Console for every slow navigation"
type: "deliverable"
status: "resolved"
blocked: false
blocked_reason: null
resolution: 'Implemented and merged in PR #821 (commit 781e8871). LRH Console now shows a native title cue, LRH Console - Loading..., when a main-window navigation runs past about 300 ms. It covers sidebar and in-page links, View menu items, Back and Forward, Reload (including URLs with a fragment), and Server > Restart, and it clears on finish, download, the next navigation, or a 20 s give-up for failed loads, which WebKit never reports. The cue starts from the navigation handler because wry on macOS reports a page load as started only when its response arrives. The main window gained no capabilities and no injected script; owner-checked in the Mac app (the cue appears and never sticks). Acceptance criterion 1 is partly met, under an explicit owner waiver (option A): the shell re-issuing navigations is ruled out in code; Restart is confirmed in the app to bypass the page script; the View menu takes the same route per the code; the sidebar case could not be reproduced once cache warm-up made pages fast; and whether WebKit stops painting during a provisional load remains unconfirmed.'
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
- "WI-LRH-CONSOLE-PAGE-SPEED"
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
- "The PR records why the --interactive page-script Loading pill does not appear in LRH Console, even for sidebar link clicks, with evidence from the app."
- "LRH Console shows a native loading cue (for example the window title or a progress indicator) whenever a main-window navigation takes longer than about 300 ms, covering sidebar and in-page links, View menu items, Back and Forward, Reload, and Server > Restart, and clears it when the page finishes or fails."
- "The main window gains no capabilities and no injected script; the cue is driven by the shell's page-load events."
- "The owner confirms in the Mac app that the cue appears on a slow first visit and never sticks."
required_evidence:
- "test_output"
- "manual_review"
- "lrh_validate"
artifacts_expected:
- "apps/desktop/src-tauri/src/shell.rs"
- "docs/how-to/lrh-console-local-dogfood.md"
---

# Native loading cue in LRH Console

## Summary

Give LRH Console its own loading cue, driven by the shell's page-load events, so that every slow navigation shows that something is happening.

## Problem / Context

`WI-LRH-CONSOLE-PAGE-SPEED` (PR #811) added a "Loading…" pill to `--interactive` pages: after 300 ms on a same-origin link click, the page dims. It works in a browser. In LRH Console, the owner saw no pill on slow (about 5 s) first visits, either from sidebar link clicks or from View > Statusboard and View > Workspace.

- **Menu items:** these navigate from the shell, so the page never sees a click. The pill code was never going to fire for them.
- **Sidebar clicks:** the cause is unconfirmed. The shell's `on_navigation` handler, which checks every main-window navigation, may re-issue or replace the navigation. Or WebKit may stop painting the old page during a provisional load.

The owner earlier chose the script approach to keep the main window capability-free. A cue in the shell keeps that property.

### Duplication search

In-repo: `apps/desktop/src-tauri/src/shell.rs` builds the main window with `on_navigation` but no page-load handler, and the page script's pill is in `src/lrh/ux/static/lrh-interactive.js`. Recommendation: proceed in the shell. Keep the page pill for browsers.

## Scope

- Diagnose the missing page pill in the app, and record the finding.
- Add a shell-side cue driven by Tauri page-load (started and finished) events for the main window.

## Required Changes

1. Confirm why the page-script pill does not show in LRH Console, with a small instrumented build if needed, and record the finding in the PR.
2. Add a main-window page-load handler in `shell.rs` that shows a cue after about 300 ms (for example, appending "Loading…" to the window title, or a native progress indicator) and clears it on finish or failure.
3. Add unit tests for the cue's state logic (start, finish, failure, overlapping navigations), and document it in the dogfood how-to.
4. Check with the owner in a branch build.

## Non-Goals

- No script injection into the main window, and no new capabilities.
- No change to the page-script pill, which stays for browser users.

## Acceptance Criteria

- The PR records why the --interactive page-script Loading pill does not appear in LRH Console, even for sidebar link clicks, with evidence from the app.
- LRH Console shows a native loading cue (for example the window title or a progress indicator) whenever a main-window navigation takes longer than about 300 ms, covering sidebar and in-page links, View menu items, Back and Forward, Reload, and Server > Restart, and clears it when the page finishes or fails.
- The main window gains no capabilities and no injected script; the cue is driven by the shell's page-load events.
- The owner confirms in the Mac app that the cue appears on a slow first visit and never sticks.

## Validation

- `scripts/format --check --diff --desktop`
- `scripts/lint --desktop`
- `scripts/test --desktop`
- `lrh validate`
- The owner checks it in a branch build of LRH Console.

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-PAGE-SPEED`, which added the page pill.
- It follows `WI-LRH-CONSOLE-CACHE-WARMUP`, which makes most first visits fast, so the cue mostly matters right after launch or restart.

## Risk Notes

- A cue that never clears is worse than none. Clear it on every terminal event, and on the next navigation's start.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md`
