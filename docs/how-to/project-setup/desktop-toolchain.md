# Setting up the desktop app toolchain

The LRH Console desktop app (`apps/desktop/`) is optional. It is a Tauri 2 shell
written in Rust, with bundled pages in plain HTML and no Node toolchain. Most
LRH work needs only Python. This guide covers setting up, testing, and running
CI for the desktop app through the same repository scripts, using `--desktop`.

## How it fits the normal workflow

- Default runs of `scripts/develop`, `scripts/test`, `scripts/lint`,
  `scripts/format`, and `scripts/version tools` are unchanged and never invoke
  or probe Rust. `scripts/test` prints one line,
  `desktop: SKIPPED (not requested; run scripts/test --desktop)`, so the skip is
  never silent.
- Adding `--desktop` includes the desktop app. Every `--desktop` mode fails, and
  never skips, when the pinned toolchain or `tauri-cli` is missing or
  mismatched.
- All Rust-aware logic is in one helper, `apps/desktop/scripts/run`. The
  top-level scripts only route `--desktop` to it. Run
  `apps/desktop/scripts/run --help` for its subcommands.

## Prerequisites

| Platform | Requirement | How to get it |
| --- | --- | --- |
| macOS | Xcode Command Line Tools | `xcode-select --install` |
| Linux (Debian/Ubuntu) | WebKitGTK and build packages | `sudo apt install libwebkit2gtk-4.1-dev build-essential curl wget file libxdo-dev libssl-dev libayatana-appindicator3-dev librsvg2-dev` |
| All | `rustup` | the official installer (`https://sh.rustup.rs`), or `scripts/develop --desktop --install-rust` |

The scripts check these prerequisites but never run `sudo` or install system
packages themselves.

## Set up

Preview first. This runs nothing, not even `pip`:

```bash
scripts/develop --desktop --dry-run
```

Then run the setup:

```bash
scripts/develop --desktop
```

This runs the normal Python develop install, then `apps/desktop/scripts/run setup`:

1. If `rustup` is missing, it prints the official install command and exits
   non-zero. To have the script run the installer instead, pass
   `--install-rust`. That flag is only accepted together with `--desktop`.
2. It installs the toolchain pinned in `apps/desktop/rust-toolchain.toml`,
   using `rustup show active-toolchain || rustup toolchain install`. Since
   rustup 1.28 the pinned toolchain is no longer auto-installed.
3. It installs the tauri-cli version pinned in `apps/desktop/toolchain.env`,
   using `cargo install tauri-cli --version =<pin> --locked`. The first install
   compiles for several minutes.
4. It checks the OS prerequisites and verifies every pin.

Confirm the result:

```bash
scripts/version tools --desktop
```

Plain `scripts/version tools` is unchanged. The `--desktop` form is strict: it
fails if any desktop pin is missing or mismatched.

## Test tiers

| Tier | Needs | Command | What it covers |
| --- | --- | --- | --- |
| 0 | Python only | `scripts/test` | Desktop config checks (pins, capabilities, CSP), `--desktop` script behavior with stubbed tools, and sdist/wheel content guards |
| 1 | Rust, headless | `scripts/test --desktop` | `cargo test`, including Tauri mock-runtime command and capability tests, and `supervisor_test.rs` against a real `lrh serve --desktop-protocol`; no window opens |
| 2 | Real window | deferred | macOS has no desktop WebDriver client, and the WebdriverIO route needs Node |
| 3 | A Mac and a person | manual checklist | Dock, menu, window, and lifecycle behavior (added with the app features) |

The supervisor tests start real `lrh serve` processes from this checkout's
`src/`. They cover start, repeated start, restart ordering, stop escalation,
readiness timeout, crash, incompatible and mismatched backends, parent loss,
and a separately started server that must stay untouched. They need a Python
interpreter that can import this checkout's dependencies. `apps/desktop/scripts/run test`
passes one to them explicitly as `LRH_DESKTOP_TEST_PYTHON`, taking it from
that variable, then `$PYTHON`, then `python3`. To run them with plain `cargo`,
set the variable yourself:

```bash
LRH_DESKTOP_TEST_PYTHON="$(command -v python3)" cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked
```

Formatting and lint follow the same pattern:

```bash
scripts/format --check --desktop
scripts/lint --desktop
```

The first command is non-mutating: it never edits tracked files. Compiling may
still write gitignored build output under `apps/desktop/src-tauri/target/`.
`scripts/lint --desktop` runs `cargo fmt --check` and `cargo clippy` with
warnings denied. It verifies the toolchain first, so a broken setup fails
before any Python check runs.

## Build and run the app

Build the macOS app bundle:

```bash
cd apps/desktop
cargo tauri build --bundles app
```

This writes `apps/desktop/src-tauri/target/release/bundle/macos/LRH Console.app`.

Until private configuration lands (`WI-LRH-CONSOLE-DESKTOP-SETTINGS`), the app
reads developer-only launch settings from its environment. Every path must be
absolute; nothing is looked up on `PATH`.

| Variable | Meaning |
| --- | --- |
| `LRH_CONSOLE_LRH_EXECUTABLE` | The `lrh` executable to supervise. |
| `LRH_CONSOLE_PYTHON` | Instead of the above, a Python interpreter that runs `-m lrh.cli.main` (for a source checkout). |
| `LRH_CONSOLE_PYTHONPATH` | Optional `PYTHONPATH` for the `LRH_CONSOLE_PYTHON` form, such as `<repo>/src`. Every entry must be absolute. |
| `LRH_CONSOLE_WORKSPACE` | The LRH workspace to serve. |

Set exactly one of the first two. The variables only reach the app when you
start its binary directly, so launch it from a terminal:

```bash
LRH_CONSOLE_PYTHON="$(command -v python3)" \
LRH_CONSOLE_PYTHONPATH="$PWD/../../src" \
LRH_CONSOLE_WORKSPACE="$(cd ../.. && pwd)" \
  "src-tauri/target/release/bundle/macos/LRH Console.app/Contents/MacOS/lrh-console"
```

The app starts its own `lrh serve --desktop-protocol` backend, and shows the
dashboard once the backend is ready. Without the settings it shows a "Backend
not configured" page.

- The Server menu starts, stops, and restarts the owned backend.
- On macOS, closing the window keeps the app and its backend running, and the
  Dock icon brings the window back. On Linux and Windows, closing the window
  quits the app.
- Quit stops the backend. A Start or Restart still pending at Quit does not
  run.

### Regenerate the app icon

The master icon is `apps/desktop/src-tauri/icons/source/lrh-icon-1024.png`: a
1024×1024 PNG with a transparent background, rendered from the Illustrator
artwork. After changing it, regenerate the desktop icon set:

```bash
cd apps/desktop
cargo tauri icon src-tauri/icons/source/lrh-icon-1024.png -o /tmp/lrh-icons
cp /tmp/lrh-icons/{32x32.png,128x128.png,128x128@2x.png,icon.icns,icon.ico,icon.png} src-tauri/icons/
```

Only the desktop files are kept. The generator's Android, iOS, and Windows
Store images are not used.

## CI

`.github/workflows/desktop.yml` runs the same commands on Ubuntu and macOS:

1. `scripts/develop --desktop`
2. `scripts/version tools --desktop`
3. `scripts/lint --desktop`
4. `scripts/test --desktop`

It runs when `apps/desktop/**`, the `--desktop`-routing scripts, the
desktop-protocol backend, or the workflow file itself change. It also runs
weekly to catch toolchain drift.

It is **not** a required check, because a required check skipped by a path
filter stays "Pending" and would block Python-only PRs. Making it required
needs an always-running aggregate check first. The Python workflows stay
Rust-free.

## Troubleshooting

- **`desktop: ERROR: pinned Rust toolchain … is not installed`**: run
  `scripts/develop --desktop`.
- **`rustc is '…', expected …`**: something is overriding the toolchain file,
  such as `RUSTUP_TOOLCHAIN` or a `rustup override`. Clear it, or run from a
  shell without the override.
- **`tauri-cli is '…', expected …`**: rerun `scripts/develop --desktop`, which
  reinstalls the pinned version.
- **Linux `missing Linux packages for: …`**: install the apt packages listed
  above; the scripts never run `sudo`.
