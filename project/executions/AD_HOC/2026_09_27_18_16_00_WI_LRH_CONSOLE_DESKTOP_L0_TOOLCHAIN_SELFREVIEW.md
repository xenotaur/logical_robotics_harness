---
execution_id: 2026_09_27_18_16_00_WI_LRH_CONSOLE_DESKTOP_L0_TOOLCHAIN_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_L0_TOOLCHAIN_SELFREVIEW)[2026-09-27T18:16:00+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/750
commit: 9eeea4422cfe3a12021b1a33b43c300a879bc896
agent: "claude_app"
instruction_source: "project/work_items/proposed/WI-LRH-CONSOLE-DESKTOP-L0.md"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-09-27T18:16:00+00:00
---

# Summary

Diff-mode `/lrh-self-review` of the uncommitted PR-1 implementation for
`WI-LRH-CONSOLE-DESKTOP-L0`: toolchain isolation, `--desktop` script modes, and
a minimal Tauri app. The diff was the working tree against `origin/main`
`40377952`. It ran from `/lrh-implement` Step 7.5 inside a human-initiated
`/lrh-execute` chain, before the PR's first push. `rerun_of` is empty because
diff-mode runs before the primary record exists.

# Result

Mode: diff. A cold-context `general-purpose` subagent received the diff, the
work item, and the repository conventions. It ran the targeted Python and
Rust tests, the helper's read-only commands, and a bash 3.2 check, and it
changed no repository files. It found no high-severity issues and reported
10 low or low-medium findings.

Top finding, re-verified directly by the invoking session:
`scripts/format --diff --desktop` ran the mutating `cargo fmt`. A deliberately
misformatted probe file was rewritten. The probe was removed afterwards.

Fixes applied after verification (report-only dispatch, no `--apply`):

1. `scripts/format` treats `--diff` as a preview, so the Rust side gets
   `fmt --check`. A new `FormatDesktopPreviewTest` asserts that only
   `cargo fmt ... -- --check` runs for `--diff`, `--check`, and both.
2. `lrh.dev.versioning` flushes stdout before running the desktop helper, so
   piped output stays in order. Confirmed with `| cat`.
3. The helper accepts `--dry-run` before or after the command.
4. The helper's help text now states accurately when pins are verified.
5. The work item's tier-1 wording now matches the implementation:
   `cargo test` runs in `scripts/test --desktop`, and fmt and clippy run in
   `scripts/lint --desktop`. CI runs both. `desktop.yml` triggers on
   `versioning.py`, as documented in the work item.
6. Failure-matrix cases now assert that stderr contains `desktop:`, so the
   failure is shown to come from the pin check. This surfaced a real gap:
   `setup` with cargo absent failed with a raw `command not found` instead of
   a clear error. Setup now checks cargo explicitly.
7. The modes test skips with a clear reason if the interpreter's directory
   contains real Rust tools.
8. The Rust ACL tests now assert that the error contains `not allowed`, so the
   denial reason is checked.
9. The toolchain check matches without a pipe (no `grep -q` SIGPIPE under
   `pipefail`), and `head -n 1` became `sed -n 1p`.

Not changed: the finding that the sdist guard scans every `dist/*.tar.gz`.
`run_release_smoke` runs `scripts/clean` first, which removes `dist/`
(`clean.py:28`), so a stale sdist cannot be present.

# Validation

After the fixes:

- `scripts/test --desktop`: `Ran 1832 tests`, OK, plus 4 Rust tests passing.
- `scripts/lint`, `scripts/format --check --diff`, `scripts/check-workflows`,
  and `lrh validate`: all clean.
- `scripts/develop --desktop`, `scripts/version tools --desktop`,
  `scripts/format --check --desktop`, `scripts/lint --desktop`, and
  `scripts/develop --desktop --dry-run`: all exit 0 on this Mac.

# Follow-up

None from this pass. The PR's first automatic review round still runs.
