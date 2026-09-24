---
resolution: null
blocked_reason: null
blocked: false
type: "deliverable"
status: "proposed"
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
required_evidence:
- "manual_review"
- "lrh_validate"
- "test_output"
- "validation_output"
id: "WI-LRH-CONSOLE-DESKTOP-L0"
title: "Build the LRH Console L0 Tauri desktop shell"
depends_on:
- "WI-LRH-CONSOLE-DESKTOP-PROTOCOL"
acceptance:
- "Mac app opens from the Dock into one default content window and completes five recorded sessions without terminal\
  \ server startup after setup."
- "Native lifecycle menus, one on-demand Settings/Details window, close/reopen, restart, Quit, and parent-crash\
  \ cleanup behave as documented."
- "Settings and recovery work without a running backend and retain last working values on invalid changes."
- "Embedded view and Chrome show the selected project, with explicit workspace mismatch and browser fallback handling."
- "Dashboard content has no native process/filesystem authority; unrelated servers remain untouched."
- "Actual Mac UI and failure evidence is recorded, CLI use remains intact, and app/canonical validation passes on\
  \ claimed platforms."
artifacts_expected:
- "apps/desktop/ (Tauri shell, native supervisor, bundled settings/state pages)"
- "docs/how-to/lrh-console-local-dogfood.md"
- "Supervisor/capability tests and actual macOS dogfood evidence"
---

# LRH Console L0 desktop shell

## Summary

Deliver a macOS dogfood app that opens from the Dock into the existing read-only
Serve view, controls its owned server through native menus, and opens one bundled
Settings / Server Details window on demand. Keep Chrome available for the same
content without daily terminal startup.

## Problem / Context

Serve and Meta are useful but command-line startup friction discourages ordinary
use. The selected interaction keeps the dashboard as the default window, with
server operations in menus. Current Serve rejects frames and mutations
(`src/lrh/serve.py:2911-2924,2983-2990` at
`8603b6514329ea242294da420aa448d2fc959fd1`), so use a direct top-level webview and
preserve the read-only boundary. The new dependency-map UI follows in L1.

### Duplication search

- In-repo: reuse Serve/Meta HTML routes and the companion desktop protocol. No
  complete Tauri app/supervisor was found in tracked source or planning artifacts.
- Sibling repos: LCATS is an intended consumer; not inspected for this capture.
- External libraries: adopt Tauri's stable top-level window/menu facilities;
  select and pin exact versions during implementation. Avoid custom browser engines.
- Recommendation: proceed with a thin shell, not a Python model or dashboard rewrite.

### Demand search

- Work items: `WI-LRH-CONSOLE-DESKTOP-PROTOCOL` is the explicit prerequisite.
- Proposals: console visual language, Serve triage, and Meta triage inform later
  refinement. The original private analyzer is an interaction reference only.
- Backlog: no desktop lifecycle request beyond the captured discussion identified;
  graph blocked-field propagation remains an L1 concern.
- Recommendation: link related designs; this shell does not satisfy the graph or
  unrelated agent runtime demands (including open PR #719).

## Scope

- One default content window plus one auxiliary Settings/Details window opened
  on demand, with native Server/View/Window and platform-appropriate Settings menus.
- Owned backend lifecycle, private explicit configuration, bundled recovery pages,
  and safe external-browser handoff using the landed protocol.
- Mac installation/development instructions and real daily-use evidence; retain
  cross-platform boundaries without claiming Linux/Windows packaging complete.

## Required Changes

1. Create a Tauri app, proposed at `apps/desktop/`, with pinned dependencies and
   documented build/dev commands. Use stable separate top-level webview windows,
   not iframes or unstable child-webview composition. Main content directly loads
   the current owned Serve origin; auxiliary content is bundled app UI.
2. Implement a Rust supervisor using the landed protocol document. Serialize
   stopped/starting/running/stopping/failed transitions; make Start idempotent and
   Restart wait for previous owned-child exit. Reject stale callbacks and wrong
   versions/workspaces. Bound readiness and stop; supervise only the child handle
   created by this app, with parent-loss behavior proven on macOS.
3. Add native Server > Start / Stop / Restart / Details, Settings, View > Dashboard
   / Reload / Open in Chrome, and window-focus actions. Enable actions by state.
   Reopen/focus an existing Settings window rather than creating duplicates.
   macOS window close keeps the app/server alive; Dock reopen restores the main
   window; Quit terminates the owned server. Closing Settings does not stop it.
4. Store executable, workspace, browser preference, and start-on-app-open setting
   in private local app configuration. Validate paths/versions/workspace and retain
   last working values on failure. Workspace switch is restart-scoped. First run
   guides explicit setup; do not rely on shell PATH/Conda activation. Browser
   configuration is a supported application choice, not an arbitrary shell command.
5. Bundle usable setup/starting/stopped/failed/incompatible pages independent of
   the Python server. Show actionable failures and bounded diagnostic history;
   avoid leaking environment secrets into logs. Server Details exposes actual
   ownership, endpoint, configured workspace, and protocol/backend versions.
6. Give loaded dashboard content no native process/filesystem commands. Restrict
   auxiliary native commands to narrow validated capabilities. Configure custom
   app-command permissions explicitly (including `AppManifest::commands` or the
   equivalent for the pinned Tauri version), not just plugin permissions; test
   that main content and bundled recovery pages cannot invoke those commands. Allow navigation
   only to approved app pages and the current exact loopback origin; remove stale
   origins on restart, handle popups, and route approved external links to a
   browser. Preserve current Serve CSP/header protections.
7. Reuse existing read-only Serve/Meta content rather than introducing L1's graph.
   Record which preview/download interactions work in the embedded view and offer
   Chrome for unsupported interactions. If Chrome is unavailable, offer a safe
   default-browser fallback with an explanation. Retain a safe route on handoff.
8. Add `docs/how-to/lrh-console-local-dogfood.md` with explicit setup, build/run,
   lifecycle expectations, recovery, limitations, and exact validation commands.
   Add automated supervisor/capability tests and a macOS manual checklist. Record
   five real use sessions with failures/friction and a recommendation for L1/L3.
   Keep normal Python installation/Serve independent of Node/Rust requirements.

## Non-Goals

- Do not add graph/phase/duration semantics, project mutation, task execution, or
  remote deployment in L0; the existing dashboard is the embedded content.
- Do not bundle Python, add login autostart, support public distribution/update
  infrastructure, or claim full Linux/Windows support in this first Mac dogfood.
- Do not adopt or stop unrelated servers, kill by port/name, or make web content
  a privileged native control surface.
- Do not require a permanently open management window or a tray-only workflow.

## Acceptance Criteria

- A locally built Mac app launches from the Dock, presents one content window by
  default, and runs five recorded sessions without terminal server startup after
  explicit initial executable/workspace setup.
- Native menus correctly start, stop, restart, show details, and reopen/focus
  windows; repeated Start never creates duplicate backends. Close/reopen and Quit
  follow the documented Mac behavior, and app crash does not leave an orphan.
- Settings remain available with a missing/crashed/incompatible backend; invalid
  configuration leaves previous working values intact and explains recovery.
- The embedded read-only view and Chrome show the same selected project; workspace
  mismatch and browser absence are explicit, not silent fallback to another project.
- Navigation/capability checks deny native commands to dashboard content; a
  separately started server remains untouched by Stop, Restart, Quit, and failure.
- Evidence includes actual Mac keyboard/window behavior and lifecycle failure
  cases; automated Linux checks alone do not close the item. CLI use stays intact.
- Canonical validation and the app-specific commands documented by this item pass
  on their claimed platforms, with any limitations recorded rather than hidden.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- Run the exact app build, supervisor, and capability-test commands added to `docs/how-to/lrh-console-local-dogfood.md` on the target Mac.
- Complete that document's manual Dock/menu/keyboard/browser/failure checklist and record five real sessions with date, app/backend version, actions, result, and remaining friction.

## Dependencies / Order

`depends_on: WI-LRH-CONSOLE-DESKTOP-PROTOCOL` is a real implementation prerequisite.
Do not couple against guessed flags before its contract lands. `blocked: false`
is the canonical metadata for a proposed item; it does not erase that dependency
or grant implementation approval. L1 is a later item and is not required to close
this bounded shell deliverable.

## Risk Notes

- A privileged webview configuration could expose native operations to repository
  content; test capability isolation, navigation, redirects, and popup behavior.
- GUI launch environment differs from a coding terminal; explicit configuration
  and first-run recovery are part of the product, not undocumented developer setup.
- Mac webview/Chrome behavior can differ; record a compatibility matrix and an
  actionable browser fallback rather than assuming browser parity.
- Process lifetime and app lifetime differ on macOS; test close versus Quit and
  parent crash explicitly. A smoke-test-only happy path is insufficient.

## Related Workstream and Designs

- `project/workstreams/proposed/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md`
- `project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md`

## Open Questions

Confirm the first Mac/CPU target, executable version support, timeout defaults
from the landed protocol, and exact pinned Tauri components during implementation.
Signing for broader distribution and Python bundling are L3 decisions. If those
become prerequisites for useful personal dogfood, propose a recorded scope change
rather than silently expanding this item.
