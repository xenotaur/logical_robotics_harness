---
id: "WI-LRH-CONSOLE-DESKTOP-SETTINGS"
title: "Add LRH Console settings, recovery pages, browser handoff, and dogfood how-to"
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
- "project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md"
- "docs/reference/desktop-server-protocol.md"
depends_on:
- "WI-LRH-CONSOLE-DESKTOP-SHELL"
blocked_by: []
expected_actions:
- "create_file"
- "edit_file"
- "run_tests"
- "write_docs"
- "create_pr"
forbidden_actions:
- "force_push"
- "delete_branch"
- "merge_pr"
- "publish_package"
- "deploy_remote_service"
- "implement_project_mutation"
- "run_lrh_agentic"
acceptance:
- "The lrh executable, workspace, browser preference, and start-on-app-open setting are stored in private local app configuration and validated. Invalid changes keep the last working values and explain recovery. A workspace switch is restart-scoped, and first run guides explicit setup without relying on shell PATH or Conda activation."
- "One on-demand Settings / Server Details window opens from Server > Details and the platform Settings menu, and reopens or focuses rather than duplicating. Closing it never stops the server. Details shows the actual ownership, endpoint, configured workspace, and protocol and backend versions."
- "Bundled setup, starting, stopped, failed, and incompatible pages work without the Python server. They show actionable failures and a bounded diagnostic history without leaking environment secrets."
- "View > Open in Chrome and approved external links hand off to a browser. The embedded view and Chrome show the same selected project. Workspace mismatch is explicit, never a silent fallback to another project. The interaction matrix is recorded, and an explained, safe default-browser fallback applies when Chrome is absent."
- "Only the Settings window can reach its narrow, validated native commands. capability_boundaries_test.rs is extended to prove that the dashboard and the recovery pages still cannot."
- "docs/how-to/lrh-console-local-dogfood.md documents setup, build/run, lifecycle, recovery, limitations, exact validation commands, and the manual macOS checklist that WI-LRH-CONSOLE-DESKTOP-DOGFOOD runs."
required_evidence:
- "manual_review"
- "lrh_validate"
- "test_output"
- "validation_output"
artifacts_expected:
- "apps/desktop/src-tauri (private configuration storage and validation, Settings/Details window, browser handoff)"
- "apps/desktop/ui (Settings/Details and setup, starting, stopped, failed, incompatible pages)"
- "apps/desktop/src-tauri/capabilities (narrow capability for the Settings window)"
- "apps/desktop/src-tauri/tests/capability_boundaries_test.rs (extended)"
- "docs/how-to/lrh-console-local-dogfood.md (with the manual macOS checklist)"
---

# LRH Console settings, recovery, and browser handoff

## Summary

Complete the L0 desktop app on top of `WI-LRH-CONSOLE-DESKTOP-SHELL`. This
item adds:

- private explicit configuration, with first-run setup;
- one on-demand Settings / Server Details window;
- the bundled recovery pages;
- browser handoff;
- the dogfood how-to and the manual checklist that
  `WI-LRH-CONSOLE-DESKTOP-DOGFOOD` runs.

## Problem / Context

This item was split out of `WI-LRH-CONSOLE-DESKTOP-SHELL` on 2026-09-30, at the
configuration/recovery boundary that the shell's own risk notes named, so that
each work item maps to one PR. It carries these Required Changes, as numbered
in the pre-split SHELL item:

- item 3 (configuration);
- item 4 (recovery pages and details);
- item 6 (browser handoff);
- the external-link routing half of item 5;
- the Settings-window extension of the item 7 tests;
- item 8 (documentation).

The GUI launch environment differs from a coding terminal. That is why
explicit configuration and first-run recovery are part of the product, rather
than being left as undocumented developer setup.

### Duplication search

- In-repo, reuse:
  - the shell's window, menus, and capability pattern;
  - the supervisor's typed errors and bounded stderr tail;
  - the existing Serve and Meta content.
- External libraries: prefer Tauri's pinned facilities for app-data paths and
  opening a browser. Pin any new plugin exactly and grant it only to the
  Settings window.
- Recommendation: proceed.

### Demand search

- Work items: `WI-LRH-CONSOLE-DESKTOP-DOGFOOD` depends on this item.
- Recommendation: proceed.

## Scope

- Private configuration, first-run setup, and the Settings/Details window.
- Recovery pages and browser handoff.
- The dogfood how-to and its checklist.

## Required Changes

1. **Configuration.**
   - Store the executable, workspace, browser preference, and
     start-on-app-open setting in private local app configuration.
   - Validate paths, versions, and the workspace. Keep the last working values
     on failure.
   - A workspace switch takes effect only after a restart.
   - First run guides explicit setup and does not rely on shell PATH or Conda
     activation.
   - The browser setting is a supported application choice, not an arbitrary
     shell command.
   - Replace the shell's developer launch settings, or keep them clearly
     developer-only.
2. **Settings / Server Details window.**
   - Open it from Server > Details and the platform Settings menu.
   - Reopen or focus the existing window instead of creating a duplicate.
     Closing it does not stop the server.
   - Details shows the actual ownership, endpoint, configured workspace, and
     protocol and backend versions.
3. **Recovery pages.**
   - Bundle setup, starting, stopped, failed, and incompatible pages that work
     without the Python server. They replace the shell's minimal status page.
   - Show actionable failures and a bounded diagnostic history, using the
     supervisor's captured output, without leaking environment secrets.
4. **Browser handoff.**
   - Add View > Open in Chrome, and route approved external links to a
     browser.
   - Record which preview and download interactions work in the embedded
     view, and offer Chrome for the ones that don't.
   - If Chrome is unavailable, offer a safe default-browser fallback with an
     explanation. Keep a safe route open on handoff.
   - Make a workspace mismatch between the embedded view and the browser
     explicit, never a silent fallback to another project.
5. **Capabilities.**
   - Restrict the Settings window's native commands to narrow, validated
     capabilities.
   - Extend `capability_boundaries_test.rs` to prove that only the Settings
     window can reach them, and that the dashboard and the recovery pages
     still cannot.
6. **Documentation.** Add `docs/how-to/lrh-console-local-dogfood.md`, covering:
   - explicit setup;
   - build and run;
   - lifecycle expectations;
   - recovery;
   - limitations;
   - the exact validation commands;
   - the manual macOS Dock, menu, keyboard, browser, and failure checklist that
     `WI-LRH-CONSOLE-DESKTOP-DOGFOOD` will run.

## Non-Goals

- Do not record the five dogfood sessions. That belongs to
  `WI-LRH-CONSOLE-DESKTOP-DOGFOOD`.
- Do not add graph semantics, project mutation, task execution, or remote
  deployment.
- Do not bundle Python, add login autostart, or support public distribution or
  update infrastructure.
- Do not make web content a privileged native control surface. Do not let
  the browser setting run arbitrary commands.

## Acceptance Criteria

- The lrh executable, workspace, browser preference, and start-on-app-open
  setting are stored in private local app configuration and validated. Invalid
  changes keep the last working values and explain recovery. A workspace
  switch is restart-scoped, and first run guides explicit setup without
  relying on shell PATH or Conda activation.
- One on-demand Settings / Server Details window opens from Server > Details
  and the platform Settings menu, and reopens or focuses rather than
  duplicating. Closing it never stops the server. Details shows the actual
  ownership, endpoint, configured workspace, and protocol and backend
  versions.
- Bundled setup, starting, stopped, failed, and incompatible pages work
  without the Python server. They show actionable failures and a bounded
  diagnostic history without leaking environment secrets.
- View > Open in Chrome and approved external links hand off to a browser. The
  embedded view and Chrome show the same selected project. Workspace mismatch
  is explicit, never a silent fallback to another project. The interaction
  matrix is recorded, and an explained, safe default-browser fallback applies
  when Chrome is absent.
- Only the Settings window can reach its narrow, validated native commands.
  capability_boundaries_test.rs is extended to prove that the dashboard and
  the recovery pages still cannot.
- docs/how-to/lrh-console-local-dogfood.md documents setup, build/run,
  lifecycle, recovery, limitations, exact validation commands, and the manual
  macOS checklist that WI-LRH-CONSOLE-DESKTOP-DOGFOOD runs.

## Validation

- `lrh validate`
- `scripts/format --check --diff --desktop`
- `scripts/lint --desktop`
- `scripts/test --desktop`
- `scripts/test` (default run, still Rust-free, prints the desktop SKIPPED line)
- `scripts/check-workflows`
- Run the exact app build and capability-test commands from `docs/how-to/lrh-console-local-dogfood.md` on the target Mac, and one smoke pass of its manual checklist.

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-DESKTOP-SHELL`.
- `WI-LRH-CONSOLE-DESKTOP-DOGFOOD` depends on this item.

## Risk Notes

- A native command exposed to the Settings window is reachable by any page
  loaded there. Keep that window on bundled pages only, and validate every
  argument.
- Mac webview and Chrome behavior can differ. Record a compatibility matrix
  and an actionable browser fallback rather than assuming parity.
- Configuration written by an older build must not silently point at the
  wrong project. Validate it at load time.

## Related Workstream and Designs

- `project/workstreams/proposed/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md`
- `project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md`
- `docs/reference/desktop-server-protocol.md`

## Open Questions

Confirm which executable versions to support, where private configuration
lives on each platform, and whether an opener plugin or a narrow custom
command handles the browser handoff. Signing and Python bundling are L3
decisions.
