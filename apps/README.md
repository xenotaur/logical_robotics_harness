# Optional applications

This directory holds optional applications built on top of LRH. They are not
part of the `lrh` Python package:

- Nothing here is imported by `src/lrh/`.
- `MANIFEST.in` prunes `apps/` from the Python sdist, and the wheel contains
  only `lrh/`. `scripts/release-smoke` checks both.
- Each application has its own pinned toolchain. Python-only contributors never
  need it: default `scripts/develop`, `scripts/test`, `scripts/lint`, and
  `scripts/format` runs do not touch these toolchains.

## Applications

- [`desktop/`](desktop/) is the LRH Console desktop shell (Tauri 2, Rust, plain
  HTML with no Node). Its toolchain landed under `WI-LRH-CONSOLE-DESKTOP-L0`;
  the app itself is being built under `WI-LRH-CONSOLE-DESKTOP-SUPERVISOR` and
  `WI-LRH-CONSOLE-DESKTOP-SHELL`.
  Set it up and test it through the repository scripts with `--desktop`; see
  [Setting up the desktop app toolchain](../docs/how-to/project-setup/desktop-toolchain.md).
