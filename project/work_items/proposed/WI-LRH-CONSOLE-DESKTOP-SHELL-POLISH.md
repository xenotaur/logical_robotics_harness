---
id: "WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH"
title: "Add Back/Forward navigation and consistent server wording to the LRH Console shell"
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
- "create_file"
- "run_tests"
- "create_pr"
forbidden_actions:
- "force_push"
- "delete_branch"
- "merge_pr"
- "publish_package"
- "deploy_remote_service"
acceptance:
- "The View menu has Back (⌘[) and Forward (⌘]) items that navigate the main window's history. They work on pages with no links of their own, such as /health and JSON routes."
- "Back and Forward never leave the current backend's origin or the app's bundled pages, and never grant web content new capabilities. The main window still has no command permissions."
- "User-facing text uses one term for the backend process. Status pages, menus, Settings, and docs agree, including the Starting… and Stopping… pages."
- "Tests cover the new menu items and their navigation policy. Format, lint, and desktop tests pass."
required_evidence:
- "test_output"
- "manual_review"
- "lrh_validate"
artifacts_expected:
- "apps/desktop/src-tauri/src/shell.rs"
- "apps/desktop/ui/status.js"
- "apps/desktop/ui/settings.html"
- "apps/desktop/ui/settings.js"
- "docs/how-to/lrh-console-local-dogfood.md"
---

# LRH Console shell polish

## Summary

Fix two shell defects from the L0 dogfood sessions:

- Pages without links are dead ends, because the app has no Back control.
- The app calls its backend both "LRH Serve" and "server".

## Problem / Context

These were found during `WI-LRH-CONSOLE-DESKTOP-DOGFOOD` and are recorded in
`project/evidence/EV-LRH-CONSOLE-DESKTOP-L0-DOGFOOD.md`:

- **D8 (session 0.2):** the owner opened `/health`, which has no links, and
  "had to guess that Delete (on macOS) would take me back". The shell's menus
  (`apps/desktop/src-tauri/src/shell.rs`, `handle_menu`) offer Dashboard,
  Meta, and Reload, but no history navigation.
- **D7 (session 1):** the owner asked whether it should be "starting LRH
  serve" or "starting LRH server". The status pages say "Starting LRH Serve…"
  and "Stopping LRH Serve…" (`apps/desktop/ui/status.js:17-18`). Menus, docs,
  and Settings say "server".

### Duplication search

- In-repo: there is no existing navigation work item. The collapsible
  sidebar request (R2) is broader and belongs to the visual-language
  proposal. This item adds only Back and Forward.
- Recommendation: proceed.

## Scope

- View > Back (⌘[) and View > Forward (⌘]) for the main window.
- One user-facing term for the backend process.

## Required Changes

1. Add Back and Forward menu items. Each should be enabled only when the
   main window can go back or forward, if the webview reports that. Otherwise
   it should do nothing when there is no history.
2. Keep the navigation policy unchanged. History navigation must pass the
   same `NavigationPolicy` checks as any other navigation, and must not add
   any capability to the main window.
3. Pick the term, for example "server" (as in "Starting LRH server…"), and
   apply it to `status.js`, menu labels, Settings text, and
   `docs/how-to/lrh-console-local-dogfood.md`. Record the choice so the
   visual-language style guide can adopt it.
4. Add tests for the menu items and for policy enforcement on history
   navigation.

## Non-Goals

- No sidebar, header bar, or other visual-language work (R1 and R2).
- No startup-page or window-state settings (R10–R13).

## Acceptance Criteria

- Back and Forward work from link-less pages and stay within policy.
- The backend is called by one term everywhere in the UI and docs.
- Tests cover the change.

## Validation

- `scripts/format --check --diff --desktop`
- `scripts/lint --desktop`
- `scripts/test --desktop`
- `lrh validate`
- A manual Mac check: open `/health`, then use ⌘[ to return.

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-DESKTOP-DOGFOOD`, whose evidence documents
  these defects.
- Independent of `WI-LRH-CONSOLE-DESKTOP-SETTINGS-POLISH`. The two can run in
  either order.

## Risk Notes

- History can contain an earlier backend's origin after a restart on a new
  port. Going back to it must be refused or redirected by the existing
  policy, never loaded.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/evidence/EV-LRH-CONSOLE-DESKTOP-L0-DOGFOOD.md`
