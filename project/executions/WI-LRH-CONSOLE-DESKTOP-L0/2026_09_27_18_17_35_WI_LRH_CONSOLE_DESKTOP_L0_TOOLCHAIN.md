---
execution_id: 2026_09_27_18_17_35_WI_LRH_CONSOLE_DESKTOP_L0_TOOLCHAIN
prompt_id: PROMPT(WI-LRH-CONSOLE-DESKTOP-L0:WI_LRH_CONSOLE_DESKTOP_L0_TOOLCHAIN)[2026-09-27T17:33:36+00:00]
work_item: WI-LRH-CONSOLE-DESKTOP-L0
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/750
commit: 9eeea4422cfe3a12021b1a33b43c300a879bc896
agent: "claude_app"
instruction_source: "project/work_items/proposed/WI-LRH-CONSOLE-DESKTOP-L0.md"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-09-27T18:17:35+00:00
---

# Summary

PR 1 of 2 for `WI-LRH-CONSOLE-DESKTOP-L0`, run through a human-initiated
`/lrh-execute` chain (`/lrh-implement` inline, then `/lrh-land`). The user
chose a two-PR structure because the item resolves only after five Mac
dogfood sessions. This PR delivers Required Changes item 9 plus a minimal
Tauri app. The branch `xenotaur/feat/wi-lrh-console-desktop-l0-toolchain` was
cut from `origin/main` `40377952`. Workstream: `WS-LRH-CONSOLE-LOCAL-DOGFOOD`.

The chain gate approved:

- Completion condition: "PR 1 merged and its execution records landed;
  WI-LRH-CONSOLE-DESKTOP-L0 stays proposed pending PR 2 and dogfood
  evidence."
- Stop-work condition: the stored default.

# Result

**Minimal app.** `apps/desktop/` holds:

- pins: `rust-toolchain.toml` (1.95.0, rustfmt and clippy), `toolchain.env`
  (tauri-cli 2.12.0), and `src-tauri/Cargo.toml` (tauri =2.12.0,
  tauri-build =2.7.0) with a committed `Cargo.lock`;
- `build.rs`, which declares the app manifest command;
- `src/lib.rs`, with `get_app_info` and mock-runtime tests;
- `tauri.conf.json` (strict CSP, bundling off), a local-only `default`
  capability for `main`, and plain HTML/CSS in `ui/`;
- the helper `scripts/run`.

**Scripts.** `--desktop` modes were added to `scripts/develop`, `test`,
`lint`, `format`, and `version tools` (`lrh.dev.versioning`):

- Default runs never touch Rust, and `scripts/test` prints the SKIPPED line.
- Every `--desktop` mode fails on a missing or mismatched pin.
- `--dry-run` runs nothing, and `--install-rust` is explicit and requires
  `--desktop`.

**Distribution guards.** `MANIFEST.in` prunes `apps`, and `release_smoke.py`
checks both the sdist and the wheel contents.

**CI.** `.github/workflows/desktop.yml` covers Ubuntu and macOS, is
path-filtered, runs weekly, and is non-required.

**Docs.** `docs/how-to/project-setup/desktop-toolchain.md` and
`apps/README.md` were added, plus links from the project-setup README,
CONTRIBUTING, and AGENTS.md.

**Tests.**

- tier 0: `tests/dev_tests/desktop_app_config_test.py`;
- stubbed matrix: `tests/scripts_tests/desktop_modes_test.py`;
- release-smoke guard tests.

**Work item.** Added a "Delivery staging" section and the `check`
subcommand, and aligned the tier-1 wording. The item stays `proposed`.

Tauri ACL facts observed while implementing:

- `generate_context!` may be expanded only once per crate, so the app and
  its tests share one `context()` function.
- The macOS bundled-page origin is `tauri://localhost`. A request from
  `http://tauri.localhost` or `http://127.0.0.1` is treated as non-local and
  denied.

Prior-art check: present in the work item, with no warnings.

The pre-push self-review is recorded in
`2026_09_27_18_16_00_WI_LRH_CONSOLE_DESKTOP_L0_TOOLCHAIN_SELFREVIEW`: nine of
its ten findings were fixed.

# Validation

Environment: macOS 26.6.2 arm64, Python 3.11.8, and a scratch venv with the
pinned Black 26.3.1 and Ruff 0.15.12 (the shared conda env is not used).
Rust 1.95.0 via rustup 1.29.0, and tauri-cli 2.12.0.

- `scripts/version tools`: OK. `scripts/check-workflows`: 10 OK.
- `scripts/format --check --diff`: clean. `scripts/lint`: exit 0.
- `scripts/test`: `Ran 1832 tests`, OK, with the SKIPPED line printed.
- `lrh validate`: 0 errors, 0 warnings.
- `scripts/develop --desktop --dry-run`: exit 0.
- `scripts/develop --desktop`: exit 0. The first `tauri-cli` install took
  5m42s.
- `scripts/version tools --desktop`, `scripts/format --check --desktop`, and
  `scripts/lint --desktop` (clippy `-D warnings`): all exit 0.
- `scripts/test --desktop`: 1832 Python tests plus 4 Rust tests, all OK.
- `scripts/release-smoke --strict-isolation`: passed, reporting "sdist has no
  apps/, wheel holds only lrh/".

# Follow-up

- PR 2 of this work item: the supervisor, menus, Settings/Details, recovery
  pages, `supervisor_test.rs`, `capability_boundaries_test.rs`, the dogfood
  how-to, and the evidence file.
- Five Mac dogfood sessions by the user.
- Deferred notes from PR #744 still apply: the acceptance wording about
  "only desktop changes", and adding `scripts/check-workflows` to the work
  item's Validation list.
