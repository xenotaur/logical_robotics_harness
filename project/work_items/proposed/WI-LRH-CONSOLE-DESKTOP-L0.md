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
- "The Python wheel, sdist, default canonical scripts, and Python CI require no Rust or Node; the sdist excludes apps/,\
  \ the wheel holds only lrh/ and its dist-info, and desktop CI runs only for desktop changes without becoming a required\
  \ check."
- "Desktop setup and checks run through the existing scripts: scripts/develop --desktop installs or verifies the pinned\
  \ toolchain, default scripts/test reports an explicit desktop SKIPPED line, and every --desktop mode fails (never\
  \ skips) when the toolchain is missing."
artifacts_expected:
- "apps/desktop/ (Tauri shell, native supervisor, bundled settings/state pages)"
- "docs/how-to/lrh-console-local-dogfood.md"
- "apps/desktop/src-tauri/tests/supervisor_test.rs"
- "apps/desktop/src-tauri/tests/capability_boundaries_test.rs"
- "apps/desktop/rust-toolchain.toml and committed apps/desktop/src-tauri/Cargo.lock (pinned toolchain)"
- "apps/README.md (optional, never imported by src/lrh)"
- "MANIFEST.in (prune apps from the Python sdist)"
- "src/lrh/dev/release_smoke.py sdist-exclusion and wheel-contents assertions, with tests/dev_tests/release_smoke_test.py\
  \ coverage"
- ".github/workflows/desktop.yml (path-filtered plus weekly scheduled, non-required desktop CI)"
- "apps/desktop/scripts/run (single desktop helper: setup, versions, fmt, lint, test; --help, --dry-run)"
- "--desktop modes for scripts/develop, scripts/test, scripts/lint, scripts/format, and scripts/version (default\
  \ behavior unchanged and Rust-free)"
- "tests/scripts_tests/desktop_modes_test.py (default runs never invoke cargo; --desktop fails when the toolchain is\
  \ missing)"
- "docs/how-to/project-setup/desktop-toolchain.md (Rust/Tauri setup, test tiers, and CI)"
- "AGENTS.md architectural-boundary line for the optional apps/ layer"
- "project/evidence/EV-LRH-CONSOLE-DESKTOP-L0-DOGFOOD.md"
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

### Toolchain placement

Four placements were compared against three requirements, checked at
`9919582b`: Python-only users need nothing new, LRH stays in one repository,
and a real Dock app is possible.

- **A self-contained `apps/desktop/` folder in this repository** (chosen). The
  wheel is built only from `src/` (`pyproject.toml:52-57`), and Python
  lint/format only look at `src/lrh` and `tests` (`scripts/lint:34`,
  `scripts/format:5`). The protocol contract also stays co-located with its
  backend.
- **A separate repository.** Rejected for now: the contract could drift, and
  planning and implementation records would be split. It stays a cheap later
  split (`git subtree split`) if the app gains its own ownership.
- **Shipping through pip** (an extra, maturin binaries, or pytauri wheels).
  Ruled out for L0: it forces per-platform wheels or a second package into the
  single pure-wheel release job (`release.yml:12-50`), and pip cannot install a
  Dock `.app`.
- **A Python-native webview instead of Tauri.** It would reverse the adopted
  Tauri decision (`00_proposal.md:49`). Revisit only if the Rust toolchain
  proves to be the measured obstacle.

Two repository facts drive the guardrails below:

- setuptools-scm adds every git-tracked file to the sdist. The sdist built at
  `9919582b` was 8.0 MB and included `project/`, `experimental/`, and
  `.claude/`, while the wheel was 736 KB and held only `lrh/`. So `apps/` must
  be pruned explicitly.
- `main` has no required status checks; its branch rules are
  `copilot_code_review`, `deletion`, and `non_fast_forward`. That makes
  path-filtered desktop CI safe today. GitHub leaves checks from a
  path-skipped workflow "Pending", which would block merges if a desktop job
  ever became required.

Tauri needs Rust, but Node only "if you intend to use a JavaScript frontend
framework". The CLI installs through Cargo, and a vanilla HTML template
exists, so L0 needs no Node.

### Developer workflow placement

Setup, testing, and CI must go through the repository's scripts and READMEs.
Canonical setup is `scripts/develop`, and validation is the fixed `scripts/...`
sequence (`CONTRIBUTING.md:121-144`, at `959af0c5`). Today `scripts/develop`
installs only Python (`scripts/develop:9`), and `scripts/test` runs only the
Python unit suite. Four ways to add Rust were compared:

- **Separate desktop commands** (`scripts/desktop` plus a README). This was
  the earlier plan. Rejected long-term: it creates a second front door that
  the canonical sequence never mentions, so desktop checks get forgotten and
  drift.
- **Desktop modes on the existing scripts** (chosen). The default runs stay
  exactly as today and Rust-free. `--desktop` adds the Rust side through one
  helper, and fails loudly if the toolchain is missing.
- **A combined toolchain manager** (mise, Nix, a devcontainer, or Rust from
  conda-forge). Rejected: none of these is installed or used here, and none
  can install Xcode Command Line Tools or Linux webkit packages. Rust from
  conda-forge would duplicate `rust-toolchain.toml`. A devcontainer cannot run
  or test the macOS Dock app, which rules it out for L0.
- **A task runner** (just, make, or cargo-make). Rejected: it duplicates the
  `scripts/` convention.

External facts behind the design, checked 2026-09-26:

- rustup 1.28 no longer auto-installs the pinned toolchain. The documented
  command is `rustup show active-toolchain || rustup toolchain install`, so
  setup needs an explicit install step.
- Tauri's `tauri::test` module (Cargo feature `test`) provides a `MockRuntime`
  with `mock_builder`, `get_ipc_response`, and `assert_ipc_response`, so
  commands and IPC can be tested headlessly on any OS.
- Tauri documents that "macOS provides no desktop WebDriver client". Its
  WebdriverIO route needs Node, which is excluded, so Mac window and menu
  behavior stays a manual checklist in L0.
- The macOS prerequisite for desktop-only development is the Command Line
  Tools. Linux needs `libwebkit2gtk-4.1-dev`, `build-essential`, and related
  packages.
- GitHub's macOS runner image ships rustup and Rust with Clippy and Rustfmt.

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
   documented build/dev commands. Use the Cargo-installed Tauri CLI (exact
   version pinned, `--locked`) and plain HTML/CSS/JS for the bundled pages, with
   no `package.json` or Node toolchain. Use stable separate top-level webview windows,
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
   Add automated tests at `apps/desktop/src-tauri/tests/supervisor_test.rs` and
   `apps/desktop/src-tauri/tests/capability_boundaries_test.rs`, plus a macOS manual
   checklist. Record five real use sessions, failures/friction, actual test
   commands/results, and a recommendation for L1/L3 in
   `project/evidence/EV-LRH-CONSOLE-DESKTOP-L0-DOGFOOD.md` using the evidence schema.
   Keep normal Python installation/Serve independent of Node/Rust requirements
   (made concrete in item 9).
9. Isolate the desktop toolchain from the Python package, using the placement
   recorded above:
   - Keep all Rust sources under `apps/desktop/`. Put `Cargo.toml` in
     `apps/desktop/src-tauri/`, never at the repository root. Pin the toolchain
     with `apps/desktop/rust-toolchain.toml` and commit `Cargo.lock`. Cargo's
     `target/` directories are already ignored by the unanchored `target/` rule
     at `.gitignore:76`; confirm it still matches rather than adding a
     duplicate.
   - Add a top-level `MANIFEST.in` with `prune apps`. Add two assertions to
     `src/lrh/dev/release_smoke.py`, next to its existing artifact checks:
     - the built sdist contains no `apps/` entries;
     - the built wheel's top-level entries are only `lrh/` and
       `lrh-<version>.dist-info/`. Today the module only locates the wheel and
       checks its filename, twine metadata, and template sources, so this adds
       the missing automated guard on wheel contents.

     That module is what `scripts/release-smoke` runs, and the
     `installed-wheel-smoke` workflow runs it on every PR, so the guards
     always execute. They are not a required check, because `main` has none
     (see "Toolchain placement"), so a failure must be treated as blocking at
     review. Cover both assertions' pass/fail logic in
     `tests/dev_tests/release_smoke_test.py` against in-memory archive
     listings, with no real build in the unit suite. Leave the wheel contents
     and `pyproject.toml` dependencies unchanged.
   - Add `.github/workflows/desktop.yml`. It runs when any of these change:
     `apps/desktop/**`, which includes the helper; the five scripts that route
     `--desktop` (`scripts/develop`, `scripts/test`, `scripts/lint`,
     `scripts/format`, `scripts/version`); or the workflow file itself. It
     also runs on a weekly cron, like `smoke.yml:8-9`, to catch toolchain
     drift.
     - It calls the same commands developers run locally:
       `scripts/develop --desktop`, then `scripts/lint --desktop` and
       `scripts/test --desktop`.
     - It has an Ubuntu job, which installs Tauri's documented apt packages,
       and a macOS job, which relies on the preinstalled rustup with the
       version pinned by `rust-toolchain.toml`.
     - Do not make it a required check unless an always-running aggregate
       check is added, because path-skipped workflows leave required checks
       pending.
     - Existing Python workflows stay unchanged and Rust-free.
   - Add `apps/README.md` stating the folder is optional, has its own
     toolchain, and is never imported by `src/lrh`. Add one line to AGENTS.md's
     architectural boundary naming `apps/` as a separate optional layer.
   - Route the desktop toolchain through the existing scripts, using the
     "Developer workflow placement" section above. Put all Rust-aware logic in
     one helper, `apps/desktop/scripts/run`, with the subcommands `setup`,
     `versions`, `fmt`, `lint`, and `test`, plus `--help` and `--dry-run`. The
     top-level scripts only parse `--desktop` and call it, which keeps them
     thin (STYLE rule 8).
     - `scripts/develop --desktop` first runs the normal Python setup, then
       `run setup`:
       - If `rustup` is missing, print the official rustup install command
         and exit non-zero. Never run a remote installer unless the separate,
         explicit `--install-rust` flag is given.
       - Run `rustup show active-toolchain || rustup toolchain install` in
         `apps/desktop/`, following the rustup 1.28 change.
       - Install the pinned Tauri CLI with
         `cargo install tauri-cli --version <exact> --locked`.
       - Check the OS prerequisites (`xcode-select -p` on macOS, the
         webkit/gtk packages on Linux) and report anything missing. Never run
         `sudo`.
     - Plain `scripts/test`, `scripts/lint`, and `scripts/format` behave
       exactly as today and never invoke cargo. `scripts/test` prints one
       explicit line, e.g.
       `desktop: SKIPPED (no Rust toolchain; run scripts/develop --desktop)`,
       so the skip is visible.
     - `scripts/test --desktop` and `--all`, and `scripts/lint --desktop` or
       `scripts/format --desktop`, also run the desktop tier. They **fail**,
       never skip, when the toolchain or a pin is missing or mismatched.
     - `scripts/format --check --desktop` is non-mutating in the source sense:
       it never edits tracked files, although compiling may write gitignored
       build artifacts under `target/`.
     - `scripts/version tools` also reports `rustup`, `rustc`, `cargo`, and
       `tauri-cli` versions and flags mismatches against the pins. It reports
       "not installed" without failing, as it already does for pyright.
     - Add `tests/scripts_tests/desktop_modes_test.py` using stubbed commands,
       with no real Rust in the unit suite. It proves that default runs never
       invoke cargo and print the SKIPPED line, and that `--desktop` exits
       non-zero when `rustup`/`cargo` are absent.
   - Organize desktop tests in tiers, all reached through the scripts above:
     - Tier 0, Python only, in default `scripts/test`: the protocol contract
       through the reference supervisor, the sdist/wheel guards, and Python
       checks over `apps/desktop` configuration such as capability files
       denying native commands to dashboard content.
     - Tier 1, Rust headless, in `scripts/test --desktop` and CI: `cargo fmt`,
       `clippy`, and `cargo test`, including `tauri::test` mock-runtime
       command/IPC and capability tests, plus supervisor tests that drive a
       real `lrh serve --desktop-protocol` child.
     - Tier 2, real-window automation, is deferred: WebDriver covers only
       Linux/Windows, and macOS would need Node.
     - Tier 3 is the manual macOS checklist and the five dogfood sessions.
   - Add `docs/how-to/project-setup/desktop-toolchain.md` covering setup via
     `scripts/develop --desktop`, OS prerequisites, the tiers, exact commands,
     the CI jobs, and troubleshooting. Link it from
     `docs/how-to/project-setup/README.md`, `apps/README.md`, and the
     CONTRIBUTING development-workflow section as the opt-in desktop sequence
     next to the unchanged default sequence.

The listed test and evidence paths are planned outputs of this implementation
item, not files delivered by the planning PR. If implementation refines their
locations, update `artifacts_expected` and this section together before closeout.

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
- Python users are unaffected by the desktop toolchain. The wheel contents and
  runtime dependencies are unchanged, the built sdist has no `apps/` entries,
  and canonical Python scripts and workflows pass on a machine without Rust or
  Node. Desktop CI runs only for desktop changes and on its weekly schedule,
  and is not a required check.
- Desktop development uses the same front door. `scripts/develop --desktop`
  sets up or verifies the pinned toolchain. Default `scripts/test` prints an
  explicit desktop SKIPPED line. `--desktop` modes run tier 1 and fail when
  the toolchain is missing, and CI calls these same commands.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- Run the exact app build, supervisor, and capability-test commands added to `docs/how-to/lrh-console-local-dogfood.md` on the target Mac.
- Complete that document's manual Dock/menu/keyboard/browser/failure checklist and record five real sessions with date, app/backend version, actions, result, and remaining friction.
- `scripts/test` on a machine or PATH without Rust: passes and prints the desktop SKIPPED line. `scripts/test tests/scripts_tests/desktop_modes_test.py` covers default and failing `--desktop` behavior with stubs.
- `apps/desktop/scripts/run --help` and `scripts/develop --desktop --dry-run` (preview only), then `scripts/develop --desktop`, `scripts/version tools`, `scripts/format --check --desktop`, `scripts/lint --desktop`, and `scripts/test --desktop` on the target Mac.
- `scripts/release-smoke --strict-isolation`: its assertions must report no `apps/` entries in the sdist and only `lrh/` plus `lrh-<version>.dist-info/` in the wheel. `scripts/test tests/dev_tests/release_smoke_test.py` covers the assertion logic.

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
- Toolchain leakage can quietly burden Python-only users. Risks include Rust or
  Node sources in the sdist, a root-level `Cargo.toml`, or desktop jobs added to
  Python workflows. The item-9 guardrails and the sdist-exclusion check are the
  controls.
- A desktop check that silently skips would look like a pass. Only the default
  run may skip, and it must say so; every explicit `--desktop` mode fails when
  the toolchain is missing, and `desktop_modes_test.py` guards both behaviors.
- Setup scripts must not install software silently or escalate privileges.
  `scripts/develop --desktop` reports missing rustup or OS packages. A remote
  installer runs only with the explicit `--install-rust` flag, and `sudo` is
  never run.
- Path-filtered desktop CI must stay non-required. Making it required without an
  always-running aggregate check would block Python-only PRs, because their
  skipped desktop checks would stay pending.

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
