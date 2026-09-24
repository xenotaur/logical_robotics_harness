---
id: "PROP-LRH-CONSOLE-LOCAL-DOGFOOD"
type: "design_proposal"
title: "LRH Console: Local Dogfood and Dependency Maps"
status: "proposed"
created_on: "2026-09-24"
updated_on: "2026-09-24"
implementation_status: "not_started"
implemented_by: []
evidence: []
supersedes: []
superseded_by: null
related_design:
- "project/design/execution_framework_mvp.md"
- "docs/explanations/workspace-and-meta-model.md"
- "project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md"
- "project/design/proposals/proposed/lrh-serve-operational-triage-mvp/00_proposal.md"
- "project/design/proposals/proposed/meta-operational-triage-semantics/00_proposal.md"
- "project/design/proposals/proposed/activity-lanes-and-observational-dashboard.md"
- "project/work_items/proposed/WI-WORK-ITEM-BLOCKED-STATE-EXPRESSIVENESS.md"
- "project/workstreams/proposed/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md"
---

# LRH Console: local dogfood and dependency maps

## Summary

Make LRH Serve, Meta, and the workstream dependency analyzer useful from the Dock
and browser without a daily terminal ritual. Build a thin Tauri desktop shell
around the existing Python service and a shared web interface, prove the local
workflow in small increments, then extend the same read model to targeted remote
experiences. The first valuable product milestone is **L0 + L1**: open the app,
select LRH or LCATS, and answer a real planning question from the dependency map.

This captures the approved design direction for review. It does not adopt the
proposal, activate implementation, or claim that the analyzer already exists in
this repository. The companion workstream contains only the first two bounded L0
implementation items; later increments remain roadmap candidates.

## Background / Motivation

The original private workstream analyzer made relationships easier to understand:
workstreams or conceptual lanes form columns, execution phases form rows, and task
cards reveal dependencies, blockers, and potential parallel work. The daily cost
of starting a command-line server currently discourages use of Serve and Meta,
even while the user works in coding applications and Chrome.

The desired direction is ambitious but the next investment should produce useful
local dogfood. Tauri is the chosen desktop direction. The normal app experience
is one content window; native menus expose server controls and open a separate
Settings / Server Details window only when needed. Chrome remains a first-class
way to view the same service. Neither a permanent control panel nor a browser-only
launcher meets the whole agreed L0 interaction.

The interaction reference is the private
[LRH workstream analyzer](https://lrh-workstream-analyzer.xenotaur.chatgpt.site/).
Its source was not inspected for this capture. Reuse of its implementation is an
open investigation, not a prerequisite or an assumption. LRH and LCATS are the
intended dogfood projects; this source review covered LRH, not the LCATS checkout.

## Prior Art Check

### Duplication search

- In-repo: extend `src/lrh/serve.py`, `src/lrh/core_state.py`, the typed control
  models, and the existing planning relationship/readiness machinery. Tracked
  source and planning searches found no complete Tauri supervisor or dependency
  map implementation. Existing Serve, Meta, prompt, and packet views are reusable.
- Sibling repos: LCATS is a named consumer; its implementation was not inspected.
  Inspect its actual control plane before claiming the shared graph is portable.
- External libraries: adopt Tauri for native shell/window/menu capabilities;
  evaluate an established graph layout/rendering library at L1. Do not implement
  a desktop toolkit, webview engine, or graph layout engine from scratch.
- Open PR context: [PR #719](https://github.com/xenotaur/logical_robotics_harness/pull/719)
  proposes local-model briefing and guarded agent experiments. It is adjacent to
  later handoff integration, not the desktop supervisor or dependency-map slice.
- Recommendation: proceed by extending the existing Python backend and adopting
  the selected shell. Keep runtime execution ownership with its existing designs.

### Demand search

- Work items: `WI-WORK-ITEM-BLOCKED-STATE-EXPRESSIVENESS` requests richer proposed
  and non-work-item blockers. Graph projection must expose current limitations;
  this proposal neither implements nor closes that policy change.
- Proposals: relate to `PROP-LRH-SERVE-OPERATIONAL-TRIAGE-MVP`,
  `PROP-LRH-CONSOLE-VISUAL-LANGUAGE`, `PROP-META-OPERATIONAL-TRIAGE-SEMANTICS`, and
  `PROP-ACTIVITY-LANES-OBSERVATIONAL-DASHBOARD`. Structural planning lanes here do
  not replace the last proposal's activity/coordination lanes.
- Backlog: `project/design/backlog.md:641` identifies inconsistent propagation of
  `WorkItem.blocked` / `blocked_reason` across builders. Audit the actual projection
  before claiming current consumers are broken or silently treating absent data
  as unblocked.
- Recommendation: link these demands as related context. No existing artifact is
  closed, superseded, adopted, or reclassified by this planning capture.

## Repository evidence

References below describe base commit
`8603b6514329ea242294da420aa448d2fc959fd1`; line numbers are for that commit.
Proposed modules and behavior later in this document are not shipped APIs.

| Existing evidence | Design consequence |
| --- | --- |
| `src/lrh/serve.py:66-130` config, host validation, and status payload | Reuse loopback service behavior; add an explicit desktop startup contract instead of treating the current health payload as ownership proof. |
| `src/lrh/serve.py:276-424` project and Meta projections | Retain Python as the source of planning semantics; extend views incrementally. |
| `src/lrh/serve.py:1624-1651` project selector fallback | Desktop configuration must validate the requested workspace explicitly; a fallback is not confirmation that the intended project loaded. |
| `src/lrh/serve.py:1673-1723` prompt/packet presentation and `1800-1816` safe capabilities | Reuse read-only workbench capabilities before adding a new execution surface. |
| `src/lrh/serve.py:2382-2426` work-item serialization | Build a versioned graph projection from typed state with field provenance. |
| `src/lrh/serve.py:2644`, `2911-2924`, `2983-2990`, `3141-3169` | Existing server rejects mutations and frames, has a restrictive CSP, and uses a foreground lifecycle. A desktop supervisor and L1 asset policy are new work. |
| `src/lrh/core_state.py:89-135`; `src/lrh/control/models.py:27-83` | Work items have no canonical phase or duration model; workstream stage is lifecycle, not a graph row. |
| `src/lrh/control/work_item_policy.py:137-146`; `src/lrh/work_items/validate.py:368-444` | Preserve current blocker policy; inspect dependency-cycle edge semantics before reusing helpers. |
| `docs/explanations/workspace-and-meta-model.md:7-25` | Workspace and Meta remain local coordination/read models, not an existing remote multiuser authority. |
| `docs/reference/cli/sessions.md:66-79`; `pyproject.toml:59-66` | Explicit executable paths have precedent; frontend asset packaging must be added and verified. |

## Design Decisions

### 1. Separate the shared product from its hosts

Options were a browser launcher, a thin desktop shell, or a desktop rewrite.
Choose the thin Tauri shell because it removes the terminal ritual while keeping
Serve usable independently and sharing the useful interface with Chrome and
future remote hosts. A launcher is a recovery option, but does not deliver the
requested embedded content view. A rewrite would duplicate mature Python models.

The proposed boundaries are:

- **Python:** load/validate project state, compute typed projections, serve the web
  application, and retain existing prompt/packet preview behavior.
- **Shared web UI:** navigation, graph/table rendering, filters, details, and
  explicitly displayed freshness. No dependency on native process commands.
- **Tauri/Rust shell:** native menus, window lifecycle, private local settings,
  executable selection, process ownership, and external-browser handoff.
- **Future remote host:** identity, project authorization, snapshot/connector
  transport, and remote service operations; not a public tunnel to the desktop.

Candidate locations are `apps/desktop/`, `src/lrh/desktop_protocol.py`,
`src/lrh/dependency_maps/`, and `ui/console/`. Settle exact module boundaries in the
corresponding implementation items. Package prebuilt web assets with Python so
ordinary `lrh serve` users do not need Node or Rust installed.

### 2. One content window by default, one auxiliary window on demand

Use stable, separate top-level webview windows. The main window displays the
existing read-only dashboard at L0. App Settings / Server Details is a bundled
page opened from the native menu and focused if already open. There is no iframe:
current Serve responses deny framing. Do not require unstable child-webview APIs.

| Surface | Proposed behavior |
| --- | --- |
| Main window | Dashboard when ready; bundled setup, starting, stopped, failed, or incompatible page otherwise. |
| Server menu | Start, Stop, Restart, Details; enabled states follow supervisor state. |
| App Settings | Executable, workspace, preferred browser, start-on-app-open preference; validate before save/restart. Use platform-appropriate Settings menu placement. |
| View menu | Dashboard, Reload, Open in Chrome (or configured browser); unavailable actions explain their state. |
| Window menu / Dock reopen | Focus or recreate the existing content window, not another backend instance. |
| macOS close window | Keep app and owned server alive; Dock click restores content. |
| Quit | Stop only the owned backend with a bounded graceful shutdown and owned-process fallback. |

Browser handoff preserves a safe in-app route when possible. If the configured
browser is absent, offer the default browser and an actionable message. Do not
launch arbitrary shell commands from a browser field. Existing preview/download
features may be limited in the embedded webview initially, with Chrome as the
explicit escape hatch; record the supported interaction matrix in L0 evidence.

Bundled state pages must remain usable when Python never starts or exits. Native
menus control recovery; loading a dashboard must not be required to stop/restart
its server. Closing the auxiliary window has no server-lifecycle effect.

### 3. Give the shell explicit process ownership and a versioned handshake

Options were parsing human CLI output, probing a fixed port, or adding a small
machine interface. Choose a documented machine interface. L0 uses a configured,
installed LRH executable and explicit workspace path. It does not assume an
interactive shell, activate Conda, or download a runtime. Bundling arrives at L3.

The protocol item must define and implement:

- A versioned startup request carrying workspace context and a unique launch ID.
- An OS-assigned loopback port and a startup response with protocol/backend
  version, launch ID, effective workspace context, actual bound endpoint, and
  ready or failed outcome. Emit ready only after binding and usable routing.
- A dedicated machine channel separated from diagnostic logs, bounded startup
  and shutdown, version negotiation, and a parent-liveness mechanism so a backend
  does not become an orphan when the app crashes. Test EOF and teardown behavior.
- Server lifecycle state: stopped, starting, running, stopping, failed. Start is
  idempotent; restart waits for the previous owned instance to exit; concurrent
  clicks are serialized. Setup/incompatible are UI conditions, not fake readiness.
- Ownership derived from the child handle/private control channel. A PID, port,
  launch ID, or successful HTTP response alone does not grant control authority.
  A launch ID correlates events; it is not an authentication secret.
- No kill-by-name or kill-by-port, and no automatic adoption of an external
  server. Any separately configured external view is clearly unowned and lacks
  Stop/Restart controls. Attaching to external servers is optional, not an L0 gate.

Keep normal foreground `lrh serve` and human CLI output compatible. Runtime
readiness means the service is reachable, not that its project validates or that
any work item is ready or authorized. Configuration changes retain the last
working values; switching the single L0 workspace requires an explicit restart.
Login autostart is a different preference from starting the server when the app
opens and is deferred.

### 4. Keep the content boundary read-only and narrow

An embedded loopback page is still web content. Give native process/filesystem
capabilities only to the bundled Settings context that requires them, with narrow
validated commands. Main content, including repository-derived text, gets no
native command access. Native menus invoke the supervisor directly.

Allow main-window navigation only to exact approved app pages and the current
owned loopback origin; route approved external links to the browser. Revoke the
old origin on restart, restrict popups, and encode repository content as data.
Avoid wildcard remote capability grants. Explicitly constrain custom invoke
commands as well as plugins: Tauri's capability documentation notes that app
commands registered with `invoke_handler` are allowed across app windows by
default unless command permissions are configured (for example through
`AppManifest::commands`). Verify denial from the main window, including its
bundled recovery pages; removing a plugin permission alone is insufficient. Enforce loopback binding and host/origin
checks appropriate to the actual transport; arbitrary web origins must not gain
access through permissive CORS. No secret tokens in URLs, stdout logs, or exports.

L1 needs scripts/assets beyond today's `default-src 'none'` CSP. Introduce a
narrow policy and same-origin packaged assets for that route, with tests; do not
relax every route or enable arbitrary inline script. Any later mutation interface
requires a separate authorization/CSRF design. L0's native server controls are
local lifecycle operations, not project mutation endpoints.

### 5. Build a typed dependency-map snapshot before interactive semantics

Options were reading YAML in the browser, reusing ad hoc Serve dictionaries, or
creating a typed projection with a versioned serialization. Choose the typed
projection. Extract reusable graph logic into a Python module rather than growing
request handlers into the domain layer. Browser and desktop consume the same
`DependencyMapSnapshot` contract and renderer.

The proposed snapshot includes schema version, project/view IDs, repository and
checkout/worktree identity, source revision/fingerprint, generation timestamp,
source references, nodes, typed edges, lane/phase assignments, diagnostics, and
provenance for derived fields. Git HEAD alone does not detect uncommitted control
file changes. Use opaque local identities; do not export absolute local paths.
An exported snapshot records filtering and freshness so omissions are explicit.

Lane and phase semantics need only enough structure to make the map truthful:

| Concept | Initial rule | Deliberately unresolved or deferred |
| --- | --- | --- |
| Lane | Default to canonical workstream grouping; optional named conceptual view mapping. Multiple/conflicting assignments produce an explicit ambiguous/unplaced result until the view selects one with a reason. | No new ownership hierarchy; no inference from directory layout. |
| Phase | Ordered view-defined rows with explicit work-item assignment and a visible Unplaced row. | Workstream `stage` is not a phase; rows do not impose dependency gates. |
| Dependency | Directed `depends_on` relationship with its source reference. | No automatic scheduling. |
| Blocker | Distinct `blocked_by` edges and explicit blocked metadata/reason where the source model supplies them. | Current policy cannot fully express proposed/non-WI blockers; show that limitation and link the existing demand. |
| Placement source | Declared, derived, or overridden, with a reason/source. | No silent heuristic placement presented as canonical data. |
| Duration | Optional later extension distinguishing effort, elapsed time, uncertainty, and capacity assumptions. | No invented duration, critical-path claim, or delivery-date prediction in L1. |

A candidate view declaration is `project/views/dependency_maps/<name>.md`. It
contains view identity, ordered lanes/phases, and mappings; it references canonical
IDs rather than duplicating tasks or dependency edges. Its exact schema, validation,
and packaging are L1 design work. Manual refresh comes first; caching shows its
source fingerprint and age, and failed refresh does not relabel old data as fresh.

### 6. Explain why work can proceed without granting permission

Keep three separate questions visible: is the service running, are dependencies
satisfied, and is this action authorized? Existing readiness policy remains
authoritative for its own assertions. Graph-derived readiness is explicitly
structural and carries diagnostics and provenance.

Detect missing references, cycles, partial source state, and ambiguous placement.
Do not let filters hide blockers and thereby turn a task ready. Preserve offscreen
predecessor counts and a way to inspect them. An abandoned predecessor is not
successful completion. Review how existing cycle helpers combine edge types before
sharing them; dependency and blocker edges have different meanings.

A wave view can show tasks whose known predecessors are satisfied. Call the result
potential structural parallelism: people, tools, shared resources, approval,
and unmodeled constraints can still prevent concurrent execution. Phases are
organizational rows, not blanket barriers. L1 must answer why a card is blocked or
eligible using source links and explicit uncertainty.

### 7. Make the original graph useful and accessible

Preserve lane columns, phase rows, dependency lines, compact task cards, gating
states, hover summaries, and expanded details. Add upstream/downstream focus,
project/workstream/status filters, blocker explanations, and a table alternative.
Details work by click, keyboard, and touch; hover is supplemental. Use text/icons
and line styles as well as color, visible focus, sufficient contrast, and reduced
motion. A wide graph on a phone needs a focused task/list mode, not just shrinking.

At L1, record three genuine planning questions across LRH and LCATS, with answers
traceable to source records. Verify cycles, missing IDs, hidden dependencies,
ambiguous lanes, absent phases, stale snapshots, and larger real project views.
Do not substitute the attractive synthetic example for the real-project pilot.

## Implementation Plan

The proposed workstream is `WS-LRH-CONSOLE-LOCAL-DOGFOOD`. Stages are usefulness
gates rather than dates or an authorization to execute the entire roadmap.

| Increment | Useful outcome | Evidence to advance |
| --- | --- | --- |
| L0a: protocol | A stable supervised Python startup/shutdown boundary. | Contract and integration tests cover ready/failure/timeout/parent loss; normal CLI remains usable. |
| L0b: desktop | Dock app with default content window, native controls, on-demand Settings/Details, and Chrome handoff. | Five real sessions without terminal startup; setup, crash, stop/restart, close/reopen, and Quit evidence on macOS. |
| L1: dependency maps | Shared real-project lane/phase graph and accessible table in app and Chrome. | Three LRH/LCATS planning questions answered with traceable evidence and adverse graph fixtures. |
| L2: daily workspace console | Several-project Meta → project → graph navigation, freshness, errors, next action. | Daily use across several projects; stable identity and no silent project fallback. |
| L3: self-contained desktop | Bundled runtime/assets and install/update/uninstall experience; Mac first, Linux then Windows. | Reboot and sleep/wake checks; runs without developer shell; platform-specific signing, packaging, and update decisions validated. |
| L4: bounded handoff | Graph → existing prompt/packet preview → coding app → evidence/review. | Several real handoff/review cycles; copying a prompt never records execution or completion. |

Initial work items:

1. `WI-LRH-CONSOLE-DESKTOP-PROTOCOL`: machine startup and lifecycle contract,
   backend integration, compatibility documentation, and failure-path tests.
2. `WI-LRH-CONSOLE-DESKTOP-L0`: Tauri shell consuming that contract, native menus,
   bundled recovery/settings pages, embedded existing Serve view, and Mac dogfood.
   It depends on the protocol item; no new dependency-map UI is required to close L0.

Create L1 and subsequent work items after the preceding gate supplies real usage
feedback. The graph remains the product objective, so L0 completion alone is not
completion of the workstream. Packaging work may move forward if executable setup
is the measured obstacle; any sequencing change should be recorded explicitly.

Remote ambitions remain compatible but are a separate, later delivery sequence:

| Increment | Target | Necessary new boundary |
| --- | --- | --- |
| R1 | Private owner-only filtered snapshot viewer; useful while laptop sleeps. | Explicit export selection, hosted authentication, freshness, revocation, and no accidentally exported paths/secrets. |
| R2 | Private live remote view. | Managed remote checkout/backend or a bounded outbound connector; disconnected state and authority documented. |
| R3 | Invited read-only collaborators. | Per-project authorization, isolation, sharing/revocation, and access tests. |
| R4 | Remote commands and collaboration. | Durable jobs, authorization at execution, conflicts/concurrency, audit, and approvals. |
| Mobile | Responsive remote/cached task view first; native iOS/Android only for demonstrated needs. | Mobile storage, credential/background constraints, touch interaction, and distribution; do not assume desktop Python sidecar/process support. |

Responsive web, Tauri mobile, and platform-native mobile remain options. Reuse the
web/read-model contracts where practical; reconsider native features only after
notification, offline, device integration, or store distribution requirements are
concrete. No mobile framework choice is a dependency of L0.

## Validation and acceptance strategy

Validate protocol and supervisor failure behavior independently of the web UI.
Automate lifecycle state transitions, wrong executable/version, duplicate start,
port allocation, stale callbacks, shutdown escalation, workspace mismatch, and
parent-liveness cleanup. Prove that an unrelated server remains untouched.

Exercise actual Tauri/WebKit navigation and capability boundaries on macOS, plus
keyboard behavior, first-run setup, unavailable backend, and browser fallback.
Linux-only unit tests are insufficient evidence for a working Dock application.
Maintain CLI regression coverage and the repository's canonical validation scripts.

For L1, use deterministic semantic fixtures plus LRH/LCATS records and compare the
same serialized snapshot in Chrome and the embedded renderer. Review graph facts,
accessibility, freshness, and responsiveness separately from visual polish.
The planning PR itself validates schema, references, sequencing, and prompt
readiness; it does not claim these future runtime tests have been run.

## Non-Goals

- Do not rewrite the Python harness, require Node/Rust for normal Python users,
  or adopt the entire future roadmap as an immediate implementation commitment.
- Do not add project writes, automatic work-item execution, merge/publish actions,
  scheduling, duration predictions, or blocker-policy changes in the initial items.
- Do not expose the local service publicly, deploy a remote app, or add multiuser
  authorization by treating loopback assumptions as a remote security model.
- Do not require runtime bundling, login autostart, a permanent control window,
  tray-only interaction, or external-process adoption to complete L0.
- Do not advance unrelated workstream/focus state or close related demands from
  this proposal's creation record.

## Risks, tradeoffs, and decision gates

The thin shell removes startup friction but adds Rust/frontend tooling and a
process lifecycle that must be tested on real platforms. L0's installed-executable
approach is the smallest dogfood step but may be too awkward for general users;
L3 is the response if that friction persists. A web-only launcher costs less but
does not satisfy the selected default content-window interaction.

A shared web renderer reduces semantic drift but does not make every platform's
window, packaging, input, and security behavior identical. A view-only phase/lane
model avoids a premature scheduling schema but cannot promise delivery dates.
Read-only remote snapshots are simpler than live collaboration but can be stale;
they must say so. No selected framework removes the need for remote identity and
project authorization. These are measured tradeoffs, not disqualifications of the
local-first sequence.

## Open Questions

- Freeze the startup channel, parent-liveness transport, protocol version policy,
  and timeout defaults in the first work item after an implementation spike.
- Confirm first Mac/CPU target and supported installed LRH version range for L0;
  exact Tauri/plugin versions are selected and pinned during implementation.
- At L1, inspect the private prototype source if available; choose renderer/layout
  dependencies based on accessibility, packaging, maintenance, and actual size.
- Finalize conceptual-lane mapping precedence, view declaration schema, and the
  first LCATS fixture from its real checkout; do not invent missing metadata.
- Establish signing identities and distribution/update policies at L3, and hosting,
  identity provider, export policy, and connectivity ownership before R1/R2.

## Cross-References

- Workstream: `project/workstreams/proposed/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`.
- Existing execution boundary: `project/design/execution_framework_mvp.md`.
- Existing workspace boundary: `docs/explanations/workspace-and-meta-model.md`.
- Prior design: `project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md`.
- Prior triage: `project/design/proposals/proposed/lrh-serve-operational-triage-mvp/00_proposal.md`.
- Prior Meta semantics: `project/design/proposals/proposed/meta-operational-triage-semantics/00_proposal.md`.
- Distinct activity lanes: `project/design/proposals/proposed/activity-lanes-and-observational-dashboard.md`.

On adoption, reconcile the relevant sections of `project/design/architecture.md`
and `project/design/execution_framework_mvp.md` with these boundaries. This review
package leaves canonical design and current focus unchanged.

External implementation references checked on 2026-09-24:

- [Tauri window menus](https://v2.tauri.app/learn/window-menu/) for native menu event handling.
- [Tauri window customization](https://v2.tauri.app/learn/window-customization/) for top-level webview window construction.
- [Tauri capabilities](https://v2.tauri.app/security/capabilities/) for per-window permissions, remote API boundaries, and custom-command defaults.
