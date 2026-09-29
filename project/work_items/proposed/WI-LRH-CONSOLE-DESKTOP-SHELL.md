---
id: "WI-LRH-CONSOLE-DESKTOP-SHELL"
title: "Build the LRH Console desktop shell: windows, menus, settings, and recovery"
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
- "WI-LRH-CONSOLE-DESKTOP-SUPERVISOR"
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
- "The locally built Mac app opens from the Dock into one default content window that loads the owned Serve origin directly, with no iframe and no child-webview composition."
- "Native Server, View, Window, and Settings menus drive the supervisor, with actions enabled by state. Settings reopens or focuses a single window. Window close keeps the app and server alive, Dock reopen restores the main window, and Quit stops the owned server."
- "Settings and the bundled setup, starting, stopped, failed, and incompatible pages work without a running backend. Invalid configuration keeps the last working values and explains recovery."
- "Dashboard content and bundled recovery pages cannot invoke native commands. Navigation is limited to approved app pages and the current exact loopback origin, popups are handled, and approved external links open in a browser."
- "The embedded view and Chrome show the same selected project. Workspace mismatch and Chrome absence are explicit, with a safe default-browser fallback."
- "capability_boundaries_test.rs passes in desktop CI, and docs/how-to/lrh-console-local-dogfood.md documents setup, build/run, lifecycle, recovery, limitations, exact validation commands, and the manual macOS checklist."
required_evidence:
- "manual_review"
- "lrh_validate"
- "test_output"
- "validation_output"
artifacts_expected:
- "apps/desktop/src-tauri (windows, native menus, settings storage, supervisor wiring, navigation policy)"
- "apps/desktop/ui (bundled Settings/Details and setup, starting, stopped, failed, incompatible pages)"
- "apps/desktop/src-tauri/capabilities (narrow capabilities for the auxiliary window)"
- "apps/desktop/src-tauri/tests/capability_boundaries_test.rs"
- "docs/how-to/lrh-console-local-dogfood.md (with the manual macOS checklist)"
- "tests/scripts_tests/desktop_modes_test.py (deferred PR #750 assertions: Linux-branch probe, exact rustup_absent message)"
- "apps/desktop/scripts/run and/or docs/how-to/project-setup/desktop-toolchain.md (test-only xdo header override renamed or documented)"
---

# LRH Console desktop shell

## Summary

Turn the minimal Tauri app from `WI-LRH-CONSOLE-DESKTOP-L0` into the daily Mac
shell:

- a Dock-launched default window showing the existing read-only Serve
  dashboard;
- native menus that drive the supervisor from
  `WI-LRH-CONSOLE-DESKTOP-SUPERVISOR`;
- one on-demand Settings / Server Details window;
- bundled recovery pages;
- strict navigation and capability boundaries;
- browser handoff.

## Problem / Context

This item was split out of `WI-LRH-CONSOLE-DESKTOP-L0` (its Required Changes
items 1 and 3–7, plus the documentation and capability-test half of item 8),
so that each work item maps to one PR.

Serve and Meta are useful, but starting them from the command line discourages
ordinary use. The chosen interaction keeps the dashboard as the default
window, with server operations in menus. Serve rejects frames and mutations
(`src/lrh/serve.py:2911-2924,2983-2990` at
`8603b6514329ea242294da420aa448d2fc959fd1`), so the app uses a direct
top-level webview and keeps the read-only boundary. The new dependency-map UI
follows in L1.

### Duplication search

- In-repo: reuse the Serve and Meta HTML routes, the landed protocol, the
  supervisor from `WI-LRH-CONSOLE-DESKTOP-SUPERVISOR`, and the capability
  pattern and mock-runtime tests from PR #750 (`apps/desktop/src-tauri/src/lib.rs`).
- External libraries: use Tauri's stable top-level window and menu facilities
  at the pinned version. Avoid custom browser engines.
- Recommendation: proceed with a thin shell, not a Python model or dashboard
  rewrite.

### Demand search

- Work items: this is a direct successor to `WI-LRH-CONSOLE-DESKTOP-L0`, and
  `WI-LRH-CONSOLE-DESKTOP-DOGFOOD` depends on it.
- Proposals: console visual language, Serve triage, and Meta triage inform
  refinement. The original private analyzer is an interaction reference only.
- Backlog: graph blocked-field propagation remains an L1 concern.
- Recommendation: proceed. This shell does not satisfy the graph or unrelated
  agent runtime demands.

### Deferred from PR #750

The final cold review of PR #750 left three small test items. They are folded
in here because this item touches the same helper and tests:

- `LinuxPrerequisitesTest` should also assert that the
  `pkg-config --exists webkit2gtk-4.1` probe ran.
- Rename `LRH_DESKTOP_XDO_HEADER` with a test-only prefix, or document it in
  `desktop-toolchain.md`.
- Pin the exact message for the `rustup_absent` failure case.

## Scope

- One default content window plus one auxiliary Settings/Details window opened
  on demand, with native Server, View, and Window menus and the
  platform-appropriate Settings menu.
- Private explicit configuration, bundled recovery pages, and safe
  external-browser handoff, all wired to the landed supervisor.
- The Mac install and development how-to and its manual checklist. Keep the
  cross-platform boundaries without claiming that Linux or Windows packaging
  is complete.

## Required Changes

1. **Windows.** Use stable, separate top-level webview windows, not iframes or
   unstable child-webview composition. The main window loads the current
   owned Serve origin directly; the auxiliary window is bundled app UI. Keep
   plain HTML/CSS/JS with no `package.json` or Node toolchain.
2. **Native menus.**
   - Add Server > Start / Stop / Restart / Details, Settings, View >
     Dashboard / Reload / Open in Chrome, and window-focus actions.
   - Enable each action by supervisor state.
   - Reopen or focus the existing Settings window rather than creating a
     duplicate.
   - On macOS, closing the window keeps the app and server alive, Dock reopen
     restores the main window, and Quit stops the owned server. Closing
     Settings does not stop the server.
3. **Configuration.**
   - Store the executable, workspace, browser preference, and start-on-app-open
     setting in private local app configuration.
   - Validate paths, versions, and the workspace, and keep the last working
     values on failure. A workspace switch takes effect only after a restart.
   - First run guides explicit setup and does not rely on shell PATH or Conda
     activation.
   - The browser setting is a supported application choice, not an arbitrary
     shell command.
4. **Recovery pages and details.**
   - Bundle setup, starting, stopped, failed, and incompatible pages that work
     without the Python server.
   - Show actionable failures and a bounded diagnostic history, using the
     supervisor's captured output, without leaking environment secrets.
   - Server Details shows the actual ownership, endpoint, configured workspace,
     and protocol and backend versions.
5. **Capabilities and navigation.**
   - Give loaded dashboard content no native process or filesystem commands.
     Restrict the auxiliary window's native commands to narrow, validated
     capabilities.
   - Configure custom app-command permissions explicitly
     (`AppManifest::commands`, as PR #750 does), not just plugin permissions.
   - Allow navigation only to approved app pages and the current exact
     loopback origin. Remove stale origins on restart, handle popups, and
     route approved external links to a browser.
   - Preserve the existing Serve CSP and header protections.
6. **Browser handoff.**
   - Reuse the existing read-only Serve and Meta content rather than
     introducing L1's graph.
   - Record which preview and download interactions work in the embedded view,
     and offer Chrome for the ones that don't.
   - If Chrome is unavailable, offer a safe default-browser fallback with an
     explanation. Keep a safe route open on handoff.
7. **Tests.** Add `apps/desktop/src-tauri/tests/capability_boundaries_test.rs`.
   It proves that main content and bundled recovery pages cannot invoke app
   commands, that only the auxiliary window can reach its narrow commands, and
   that navigation and popups outside the allowed set are refused. Extend the
   mock-runtime tests from PR #750 rather than duplicating them. Also apply
   the three deferred PR #750 test items above.
8. **Documentation.** Add `docs/how-to/lrh-console-local-dogfood.md`, covering:
   - explicit setup;
   - build and run;
   - lifecycle expectations;
   - recovery;
   - limitations;
   - the exact validation commands;
   - the manual macOS Dock, menu, keyboard, browser, and failure checklist that
     `WI-LRH-CONSOLE-DESKTOP-DOGFOOD` will run.

## Non-Goals

- Do not add graph, phase, or duration semantics, project mutation, task
  execution, or remote deployment. The existing dashboard is the embedded
  content.
- Do not bundle Python, add login autostart, or support public distribution or
  update infrastructure. Do not claim full Linux or Windows support.
- Do not adopt or stop unrelated servers, kill by port or name, or make web
  content a privileged native control surface.
- Do not require a permanently open management window or a tray-only
  workflow.
- Do not record the five dogfood sessions. That belongs to
  `WI-LRH-CONSOLE-DESKTOP-DOGFOOD`.

## Acceptance Criteria

- The Mac app opens from the Dock into one default content window that loads
  the owned Serve origin directly.
- Native menus start, stop, restart, show details, and reopen or focus
  windows. Repeated Start never creates a duplicate backend, and close,
  reopen, and Quit follow the documented Mac behavior.
- Settings and the recovery pages work without a running backend. Invalid
  configuration keeps the previous working values and explains recovery.
- Dashboard content and recovery pages cannot invoke native commands, and
  navigation is limited to approved pages and the current exact loopback
  origin.
- The embedded view and Chrome show the same selected project. Workspace
  mismatch and browser absence are explicit, not a silent fallback to another
  project.
- `capability_boundaries_test.rs` passes in desktop CI, and the dogfood how-to,
  including its checklist, is complete.

## Validation

- `lrh validate`
- `scripts/format --check --diff --desktop`
- `scripts/lint --desktop`
- `scripts/test --desktop`
- `scripts/test` (default run, still Rust-free, prints the desktop SKIPPED line)
- `scripts/check-workflows`
- Run the exact app build and capability-test commands from `docs/how-to/lrh-console-local-dogfood.md` on the target Mac, and one smoke pass of its manual checklist.

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-DESKTOP-SUPERVISOR`.
- `WI-LRH-CONSOLE-DESKTOP-DOGFOOD` depends on this item.

## Risk Notes

- A privileged webview configuration could expose native operations to
  repository content. Test capability isolation, navigation, redirects, and
  popup behavior.
- The GUI launch environment differs from a coding terminal. Explicit
  configuration and first-run recovery are part of the product, not
  undocumented developer setup.
- Mac webview and Chrome behavior can differ. Record a compatibility matrix
  and an actionable browser fallback rather than assuming parity.
- This is the largest remaining slice. If it proves too big to review as one
  PR, split it again at the configuration/recovery boundary before starting,
  rather than landing several PRs under this one item.

## Related Workstream and Designs

- `project/workstreams/proposed/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md`
- `project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md`
- `docs/reference/desktop-server-protocol.md`

## Open Questions

Confirm the first Mac/CPU target, which executable versions to support, and
the exact pinned Tauri components during implementation. Signing for broader
distribution and Python bundling are L3 decisions.
