---
id: "WI-LRH-CONSOLE-DESKTOP-SHELL"
title: "Build the LRH Console desktop shell: windows, lifecycle menus, and boundaries"
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
- "implement_lrh_console_desktop_settings"
acceptance:
- "The locally built Mac app opens from the Dock into one default content window. While the owned backend runs, the window loads its Serve origin directly, with no iframe and no child-webview composition. Otherwise it shows one minimal bundled status page."
- "Native Server > Start / Stop / Restart, View > Dashboard / Reload, and Window focus actions drive the supervisor, and each is enabled by state. Repeated Start never creates a duplicate backend. Menu actions run off the UI thread and are serialized, so a Start never returns a stale error or a crash from an earlier launch. Window close keeps the app and server alive, Dock reopen restores the main window, and Quit stops the owned server within the supervisor's bounds."
- "Dashboard content and the bundled status page cannot invoke native commands. Navigation is limited to bundled app pages and the current exact loopback origin. A stale origin is dropped on restart, and popups and external links are refused rather than opened in the app."
- "capability_boundaries_test.rs passes in desktop CI, covering command denial, the allowed navigation set, stale-origin removal, and popup refusal."
- "A developer can launch the app against an explicit lrh executable and workspace through documented developer-only settings, never through shell PATH lookup."
required_evidence:
- "manual_review"
- "lrh_validate"
- "test_output"
- "validation_output"
artifacts_expected:
- "apps/desktop/src-tauri (main window, native lifecycle menus, supervisor wiring, navigation policy, developer launch settings)"
- "apps/desktop/ui (one minimal bundled status page)"
- "apps/desktop/src-tauri/capabilities (dashboard and bundled page get no app commands)"
- "apps/desktop/src-tauri/tests/capability_boundaries_test.rs"
- "docs/how-to/project-setup/desktop-toolchain.md (developer launch of the shell)"
- "tests/scripts_tests/desktop_modes_test.py (deferred PR #750 assertions: Linux-branch probe, exact rustup_absent message)"
- "apps/desktop/scripts/run and/or docs/how-to/project-setup/desktop-toolchain.md (test-only xdo header override renamed or documented)"
---

# LRH Console desktop shell

## Summary

Turn the minimal Tauri app from `WI-LRH-CONSOLE-DESKTOP-L0` into a Dock app
that owns its backend. It has three parts:

- a default window showing the existing read-only Serve dashboard;
- native lifecycle menus driving the supervisor from
  `WI-LRH-CONSOLE-DESKTOP-SUPERVISOR`;
- strict navigation and capability boundaries.

Private configuration, Settings/Details, the full recovery pages, browser
handoff, and the dogfood how-to follow in
`WI-LRH-CONSOLE-DESKTOP-SETTINGS`.

## Problem / Context

This item was split out of `WI-LRH-CONSOLE-DESKTOP-L0`, then split again on
2026-09-30 at the configuration/recovery boundary so that each work item maps
to one PR. It keeps the lifecycle and security core, which the Settings work
builds on:

- original L0 items 1 (windows), 2 (menus), and 5 (capabilities and
  navigation);
- the capability-test half of item 7.

Serve and Meta are useful, but starting them from the command line
discourages ordinary use. The chosen interaction keeps the dashboard as the
default window, with server operations in menus. Serve rejects frames and
mutations (`src/lrh/serve.py:2911-2924,2983-2990` at
`8603b6514329ea242294da420aa448d2fc959fd1`), so the app uses a direct
top-level webview and keeps the read-only boundary. The new dependency-map UI
follows in L1.

### Duplication search

- In-repo: reuse these rather than rebuilding them:
  - the Serve and Meta HTML routes;
  - the landed protocol;
  - `apps/desktop/src-tauri/src/supervisor.rs`, from PR #758;
  - the capability pattern and mock-runtime tests in
    `apps/desktop/src-tauri/src/lib.rs`, from PR #750.
- External libraries: use Tauri's stable top-level window and menu facilities
  at the pinned version. Avoid custom browser engines.
- Recommendation: proceed with a thin shell, not a Python model or dashboard
  rewrite.

### Demand search

- Work items: this is a direct successor to `WI-LRH-CONSOLE-DESKTOP-L0`.
  `WI-LRH-CONSOLE-DESKTOP-SETTINGS` depends on it.
- Proposals: console visual language, Serve triage, and Meta triage inform
  refinement.
- Recommendation: proceed. This shell does not satisfy the graph or unrelated
  agent runtime demands.

### Deferred from earlier PRs

These three small test items are left over from PR #750's final cold review:

- `LinuxPrerequisitesTest` should also assert that the
  `pkg-config --exists webkit2gtk-4.1` probe ran.
- Rename `LRH_DESKTOP_XDO_HEADER` with a test-only prefix, or document it in
  `desktop-toolchain.md`.
- Pin the exact message for the `rustup_absent` failure case.

These two items are left over from PR #758's final cold review, and affect
how the menus drive the supervisor:

- A Start queued behind a failing launch returns that launch's error, even if
  a Stop ran in between.
- A narrow Restart-then-crash race makes a queued Start return
  `ExitedUnexpectedly`.

Serialize menu actions so that neither case is reachable from the UI. This is
required, not optional.

## Scope

- One default content window, with native Server, View, and Window menus.
- Supervisor wiring for the app lifecycle, including close, reopen, and Quit.
- Navigation and capability boundaries, with tests.
- Developer-only launch settings, which `WI-LRH-CONSOLE-DESKTOP-SETTINGS`
  replaces with private configuration.

## Required Changes

1. **Main window.**
   - Use a stable top-level webview window, not iframes or unstable
     child-webview composition.
   - While the owned backend runs, the window loads its verified endpoint URL
     directly.
   - Otherwise it shows one minimal bundled status page: stopped, starting,
     or failed, with the error code. Keep plain HTML/CSS/JS with no
     `package.json` or Node toolchain.
2. **Native lifecycle menus.**
   - Add Server > Start / Stop / Restart, View > Dashboard / Reload, and
     window-focus actions.
   - Enable each action by supervisor state.
   - Run menu actions off the UI thread, and serialize them so that the two
     PR #758 edge cases above cannot arise from the UI. Serialization is
     required; documenting the behavior instead is not acceptable.
   - On macOS, closing the window keeps the app and server alive, Dock reopen
     restores the main window, and Quit stops the owned server within the
     supervisor's bounds.
3. **Developer launch settings.**
   - Read the `lrh` executable (or interpreter plus module) and the
     workspace from explicit developer-only settings, such as documented
     environment variables. Never resolve them through shell PATH lookup.
   - Document this in `docs/how-to/project-setup/desktop-toolchain.md` as a
     developer path that the private configuration in
     `WI-LRH-CONSOLE-DESKTOP-SETTINGS` replaces.
4. **Capabilities and navigation.**
   - Give loaded dashboard content and the bundled status page no native
     process or filesystem commands.
   - Configure custom app-command permissions explicitly
     (`AppManifest::commands`, as PR #750 does), not just plugin permissions.
   - Allow navigation only to bundled app pages and the current exact
     loopback origin, and remove a stale origin on restart.
   - Refuse popups and external links in the app. The browser handoff that
     opens them outside belongs to `WI-LRH-CONSOLE-DESKTOP-SETTINGS`.
   - Preserve the existing Serve CSP and header protections.
5. **Tests.** Add `apps/desktop/src-tauri/tests/capability_boundaries_test.rs`.
   It proves that main content and the bundled status page cannot invoke app
   commands. It also proves that navigation outside the allowed set, stale
   origins after a restart, and popups are refused. Extend the mock-runtime
   tests from PR #750 rather than duplicating them. Also apply the three
   deferred PR #750 test items above.

## Non-Goals

- No private configuration storage, first-run setup, or Settings/Details
  window.
- No full recovery pages, browser handoff, or dogfood how-to. These belong to
  `WI-LRH-CONSOLE-DESKTOP-SETTINGS`.
- Do not add graph, phase, or duration semantics, project mutation, task
  execution, or remote deployment.
- Do not bundle Python, add login autostart, or support public distribution or
  update infrastructure. Do not claim full Linux or Windows support.
- Do not adopt or stop unrelated servers, kill by port or name, or make web
  content a privileged native control surface.

## Acceptance Criteria

- The locally built Mac app opens from the Dock into one default content
  window. While the owned backend runs, the window loads its Serve origin
  directly, with no iframe and no child-webview composition. Otherwise it
  shows one minimal bundled status page.
- Native Server > Start / Stop / Restart, View > Dashboard / Reload, and
  Window focus actions drive the supervisor, and each is enabled by state.
  Repeated Start never creates a duplicate backend. Menu actions run off the
  UI thread and are serialized, so a Start never returns a stale error or a
  crash from an earlier launch. Window close keeps the app and server alive,
  Dock reopen restores the main window, and Quit stops the owned server within
  the supervisor's bounds.
- Dashboard content and the bundled status page cannot invoke native commands.
  Navigation is limited to bundled app pages and the current exact loopback
  origin. A stale origin is dropped on restart, and popups and external links
  are refused rather than opened in the app.
- capability_boundaries_test.rs passes in desktop CI, covering command denial,
  the allowed navigation set, stale-origin removal, and popup refusal.
- A developer can launch the app against an explicit lrh executable and
  workspace through documented developer-only settings, never through shell
  PATH lookup.

## Validation

- `lrh validate`
- `scripts/format --check --diff --desktop`
- `scripts/lint --desktop`
- `scripts/test --desktop`
- `scripts/test` (default run, still Rust-free, prints the desktop SKIPPED line)
- `scripts/check-workflows`
- Build the app on the target Mac, then launch it with the developer settings. Do one smoke pass of Start, Stop, Restart, window close and Dock reopen, and Quit, and record the result in the execution record.

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-DESKTOP-SUPERVISOR` (resolved).
- `WI-LRH-CONSOLE-DESKTOP-SETTINGS` depends on this item.

## Risk Notes

- A privileged webview configuration could expose native operations to
  repository content. Test capability isolation, navigation, redirects, and
  popup behavior.
- A supervisor call made on the UI thread would freeze the app for up to the
  startup budget, so menu actions must run off that thread.
- The developer launch settings must not become the product configuration
  path. `WI-LRH-CONSOLE-DESKTOP-SETTINGS` replaces them.

## Related Workstream and Designs

- `project/workstreams/proposed/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md`
- `project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md`
- `docs/reference/desktop-server-protocol.md`

## Open Questions

Confirm the first Mac/CPU target and the exact pinned Tauri components
(menus, window events) during implementation.
