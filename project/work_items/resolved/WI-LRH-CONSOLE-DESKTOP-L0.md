---
resolution: 'Delivered by PR #750 (merge 9eeea442, closeout 4f0f7a51): pinned Rust/Tauri toolchain, --desktop script modes, desktop CI, sdist/wheel guards, and a minimal Tauri app with local-only capabilities. Supervisor, shell, and dogfood scope moved to WI-LRH-CONSOLE-DESKTOP-SUPERVISOR, WI-LRH-CONSOLE-DESKTOP-SHELL, and WI-LRH-CONSOLE-DESKTOP-DOGFOOD.'
blocked_reason: null
blocked: false
type: "deliverable"
status: "resolved"
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
title: "Set up the LRH Console desktop toolchain and minimal Tauri app"
depends_on:
- "WI-LRH-CONSOLE-DESKTOP-PROTOCOL"
acceptance:
- "A minimal Tauri app under apps/desktop/ builds with the pinned toolchain. It has one bundled placeholder window, one read-only app command, and a local-only capability, and mock-runtime tests prove that an unlisted window and a loopback origin in the main window are denied app commands."
- "The Python wheel, sdist, default canonical scripts, and Python CI require no Rust or Node; the sdist excludes apps/,\
  \ the wheel holds only lrh/ and its dist-info, and desktop CI runs only for desktop changes without becoming a required\
  \ check."
- "Desktop setup and checks run through the existing scripts: scripts/develop --desktop installs or verifies the pinned\
  \ toolchain, default scripts/test reports an explicit desktop SKIPPED line, and every --desktop mode fails (never\
  \ skips) when the toolchain is missing."
artifacts_expected:
- "apps/desktop/ (minimal Tauri app: one bundled placeholder window, get_app_info command, local-only capability)"
- "apps/desktop/rust-toolchain.toml and committed apps/desktop/src-tauri/Cargo.lock (pinned toolchain)"
- "apps/README.md (optional, never imported by src/lrh)"
- "MANIFEST.in (prune apps from the Python sdist)"
- "src/lrh/dev/release_smoke.py sdist-exclusion and wheel-contents assertions, with tests/dev_tests/release_smoke_test.py\
  \ coverage"
- ".github/workflows/desktop.yml (path-filtered plus weekly scheduled, non-required desktop CI)"
- "apps/desktop/scripts/run (single desktop helper: setup, check, versions, fmt, lint, test; --help, --dry-run)"
- "--desktop modes for scripts/develop, scripts/test, scripts/lint, scripts/format, and scripts/version tools (default\
  \ behavior and output unchanged and Rust-free)"
- "tests/scripts_tests/desktop_modes_test.py (default runs never invoke cargo; every --desktop mode fails on a missing or\
  \ mismatched toolchain or tauri-cli pin; dry-run and --install-rust paths covered)"
- "docs/how-to/project-setup/desktop-toolchain.md (Rust/Tauri setup, test tiers, and CI)"
- "AGENTS.md architectural-boundary line for the optional apps/ layer"
---

# LRH Console desktop toolchain and minimal app

## Summary

Set up the optional Rust/Tauri toolchain for the LRH Console desktop app, in
this repository but isolated from the Python package, and land a minimal
Tauri app that proves the toolchain, the scripts, CI, and the capability
boundary end to end. Python-only users need nothing new.

## Scope split

This item originally covered the whole L0 desktop shell. It was narrowed on
2026-09-29 so that each work item maps to one PR. It now covers only what
PR #750 delivered: the original Required Changes item 9, plus the minimal app
from its first delivery stage. The rest of the original scope moved to:

- `WI-LRH-CONSOLE-DESKTOP-SUPERVISOR`: original item 2, the Rust supervisor
  for the owned backend, with `supervisor_test.rs`.
- `WI-LRH-CONSOLE-DESKTOP-SHELL`: original items 1 and 3–7, plus the
  documentation and capability-test half of item 8. That covers windows,
  menus, Settings/Details, configuration, recovery pages, navigation and
  capability limits, browser handoff, `capability_boundaries_test.rs`, and
  `docs/how-to/lrh-console-local-dogfood.md`.
- `WI-LRH-CONSOLE-DESKTOP-DOGFOOD`: the evidence half of item 8. That is the
  five recorded Mac sessions, the manual checklist run, and
  `project/evidence/EV-LRH-CONSOLE-DESKTOP-L0-DOGFOOD.md`.

The L0 evidence gate in `WS-LRH-CONSOLE-LOCAL-DOGFOOD` is unchanged. It is
now satisfied by those three items together, not by this one.

## Problem / Context

The LRH Console desktop app needs Rust and Tauri, but most LRH users only want
the Python package. The toolchain has to be available to desktop developers
through the same scripts and READMEs as everything else, without burdening
Python-only work or leaking into the published package.

### Duplication search

- In-repo: no Rust sources, Cargo manifest, or desktop scripts existed before
  this item.
- External libraries: adopt Tauri's Cargo-installed CLI and a vanilla
  HTML/CSS/JS frontend with no Node. Pin exact versions.
- Recommendation: proceed with a self-contained `apps/desktop/`.

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
- Recommendation: proceed. The successor items above carry the app features.

## Scope

- A minimal Tauri app under `apps/desktop/` with pinned dependencies.
- Isolation of the desktop toolchain from the Python package, desktop CI, and
  `--desktop` modes on the existing scripts.
- Toolchain documentation. App features are out of scope; see "Scope split".

## Required Changes

1. Create a minimal Tauri app at `apps/desktop/` with pinned dependencies and
   documented build and dev commands:
   - Use the Cargo-installed Tauri CLI, with its exact version pinned and
     `--locked`, and plain HTML/CSS/JS for the bundled page, with no
     `package.json` or Node toolchain.
   - Provide one bundled placeholder window, one read-only app command, and a
     local-only capability.
   - Configure the app-command permissions explicitly through
     `AppManifest::commands`.
   - Its mock-runtime tests prove that an unlisted window, and a loopback
     origin in the main window, are both denied app commands.
2. Isolate the desktop toolchain from the Python package, using the placement
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
     `scripts/format`, `scripts/version`, plus `src/lrh/dev/versioning.py`,
     which implements the strict version check); the Python backend that the tier-1
     supervisor tests drive (`src/lrh/desktop_protocol.py`,
     `src/lrh/desktop_supervisor.py`, `src/lrh/serve.py`); or the workflow file
     itself. A backend protocol change must run the Rust integration tests in
     the same PR. It also runs on a weekly cron, like `smoke.yml:8-9`, to
     catch toolchain drift.
     - It calls the same commands developers run locally:
       `scripts/develop --desktop`, then the strict
       `scripts/version tools --desktop`, `scripts/lint --desktop`, and
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
     `check`, `versions`, `fmt`, `lint`, and `test`, plus `--help` and
     `--dry-run`. `check` is a quiet pin preflight: `scripts/lint --desktop`
     and `scripts/version tools --desktop` run it first, so a broken toolchain
     fails before any Python check. The top-level scripts only parse
     `--desktop` and call the helper, which keeps them thin (STYLE rule 8).
     - Each top-level script parses its own flags (`--desktop`,
       `--dry-run`, `--install-rust`) before anything else runs, and before
       any remaining arguments pass through. Today `scripts/test` hands its
       first unrecognized argument to unittest as a test target
       (`scripts/test:20-32`), so the new flags must be consumed first.
     - `scripts/develop --desktop --dry-run` is preview-only. It is handled
       before the Python setup: it prints the Python install command and the
       desktop setup commands (via `run setup --dry-run`), then exits 0
       without running `pip` or any Rust command.
     - Otherwise, `scripts/develop --desktop` first runs the normal Python
       setup, then `run setup`:
       - If `rustup` is missing, print the official rustup install command
         and exit non-zero. This is the default refusal.
       - `scripts/develop --desktop --install-rust`, which passes through to
         `run setup --install-rust`, is the only path that runs the official
         rustup installer. It must be given explicitly each time.
         `--install-rust` without `--desktop` is rejected with a usage error
         and a non-zero exit, never silently ignored.
       - Run `rustup show active-toolchain || rustup toolchain install` in
         `apps/desktop/`, following the rustup 1.28 change.
       - Install the pinned Tauri CLI with
         `cargo install tauri-cli --version <exact> --locked`.
       - Check the OS prerequisites (`xcode-select -p` on macOS, the
         webkit/gtk packages on Linux) and report anything missing. Never run
         `sudo`.
     - Plain `scripts/test`, `scripts/lint`, and `scripts/format` behave
       exactly as today and never invoke or probe cargo or rustup.
       `scripts/test` always prints one explicit line, whether or not Rust is
       installed, e.g.
       `desktop: SKIPPED (not requested; run scripts/test --desktop)`,
       so the skip is visible and never depends on a toolchain probe.
     - `scripts/test --desktop` runs the Python suite plus the desktop tier.
       There is no separate `--all` mode. `scripts/lint --desktop` and
       `scripts/format --desktop` likewise run the Python checks plus the
       Rust ones. All `--desktop` modes **fail**, never skip, when the
       toolchain, the pinned toolchain version, or the pinned `tauri-cli`
       version is missing or mismatched.
     - `scripts/format --check --desktop` is non-mutating in the source sense:
       it never edits tracked files, although compiling may write gitignored
       build artifacts under `target/`.
     - Plain `scripts/version tools` stays exactly as today, with no Rust
       probes and unchanged output. `scripts/version tools --desktop` is the
       strict form: it additionally reports `rustup`, `rustc`, `cargo`, and
       `tauri-cli` versions against the pins, and exits non-zero if any is
       missing or mismatched. Desktop CI uses the strict form.
     - Add `tests/scripts_tests/desktop_modes_test.py` using stubbed commands,
       with no real Rust in the unit suite. It must prove that:
       - default `scripts/test`, `lint`, `format`, and `version tools` never
         invoke cargo or rustup, and `scripts/test` prints the SKIPPED line;
       - every `--desktop` mode (`develop`, `test`, `lint`, `format`,
         `version tools`) exits non-zero on each failure case: `rustup`
         absent, `cargo` absent, pinned toolchain not installed, toolchain
         version mismatched, and `tauri-cli` missing or mismatched;
       - `scripts/develop --desktop --dry-run` runs neither `pip` nor any
         Rust command;
       - without `--install-rust`, a missing rustup is refused with a
         non-zero exit and the printed install command, and with it the
         (stubbed) official installer is invoked;
       - `--install-rust` without `--desktop` exits non-zero with a usage
         error.
   - Organize desktop tests in tiers, all reached through the scripts above:
     - Tier 0, Python only, in default `scripts/test`: the protocol contract
       through the reference supervisor, the sdist/wheel guards, and Python
       checks over `apps/desktop` configuration such as capability files
       denying native commands to dashboard content.
     - Tier 1, Rust headless: `cargo test` in `scripts/test --desktop`, and
       `cargo fmt --check` plus `clippy` in `scripts/lint --desktop`. CI runs
       both. Tests include `tauri::test` mock-runtime command/IPC and
       capability tests, plus supervisor tests that drive a real
       `lrh serve --desktop-protocol` child.
     - Tier 2, real-window automation, is deferred: WebDriver covers only
       Linux/Windows, and macOS would need Node.
     - Tier 3 is the manual macOS checklist and the five dogfood sessions.
   - Add `docs/how-to/project-setup/desktop-toolchain.md` covering setup via
     `scripts/develop --desktop`, OS prerequisites, the tiers, exact commands,
     the CI jobs, and troubleshooting. Link it from
     `docs/how-to/project-setup/README.md`, `apps/README.md`, and the
     CONTRIBUTING development-workflow section as the opt-in desktop sequence
     next to the unchanged default sequence.


## Non-Goals

- No supervisor, native menus, Settings/Details window, recovery pages,
  navigation policy, browser handoff, or dogfood evidence. These moved to the
  successor items.
- Do not bundle Python, publish the app, or claim Linux or Windows app
  support.
- Do not add Rust or Node requirements to the Python package, its default
  scripts, or its workflows.

## Acceptance Criteria

- A minimal Tauri app under `apps/desktop/` builds with the pinned toolchain,
  and its mock-runtime tests deny app commands to an unlisted window and to a
  loopback origin in the main window.
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
- `scripts/check-workflows`
- `scripts/test` on a machine or PATH without Rust passes and prints the desktop SKIPPED line.
- `scripts/test tests/scripts_tests/desktop_modes_test.py` uses stubs to cover default runs, every failure case listed in item 2 (absent rustup or cargo, missing or mismatched pinned toolchain, missing or mismatched `tauri-cli`) for each `--desktop` mode, the dry-run path, and the `--install-rust` paths, including its rejection without `--desktop`.
- `apps/desktop/scripts/run --help` and `scripts/develop --desktop --dry-run` (preview only; confirm no `pip` or Rust command ran), then `scripts/develop --desktop`, `scripts/version tools --desktop`, `scripts/format --check --desktop`, `scripts/lint --desktop`, and `scripts/test --desktop` on the target Mac.
- `scripts/release-smoke --strict-isolation`: its assertions must report no `apps/` entries in the sdist and only `lrh/` plus `lrh-<version>.dist-info/` in the wheel. `scripts/test tests/dev_tests/release_smoke_test.py` covers the assertion logic.

## Dependencies / Order

`depends_on: WI-LRH-CONSOLE-DESKTOP-PROTOCOL` was a real prerequisite and is
resolved. `WI-LRH-CONSOLE-DESKTOP-SUPERVISOR` depends on this item.

## Risk Notes

- Toolchain leakage can quietly burden Python-only users. Risks include Rust or
  Node sources in the sdist, a root-level `Cargo.toml`, or desktop jobs added
  to Python workflows. The item-2 guardrails and the sdist-exclusion check are
  the controls.
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
