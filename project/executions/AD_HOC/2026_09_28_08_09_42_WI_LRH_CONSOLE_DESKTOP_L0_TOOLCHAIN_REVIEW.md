---
execution_id: 2026_09_28_08_09_42_WI_LRH_CONSOLE_DESKTOP_L0_TOOLCHAIN_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_L0_TOOLCHAIN_REVIEW)[2026-09-28T06:25:35+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/750
commit: 
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/750"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-09-28T08:09:42+00:00
---

# Summary

Review-response round 1 for PR #750 (PR 1 of `WI-LRH-CONSOLE-DESKTOP-L0`).
It covers the one failing CI check and the first-push hosted reviews:

- CI: `desktop (macos-latest)` failed, which fired the run's stop-work
  condition. The user chose to fix it in this PR.
- Codex left one inline thread.
- Copilot put four findings in its review body, with no inline threads.

The user approved the plan: fix the CI failure and findings 1–4, and dismiss
finding 5 with a rationale.

# Result

1. **CI failure (`c11d19d5`).** The failing test was
   `test_scripts_validate_log_mode`. The cause was already in `main`:
   `scripts/validate` expanded an empty `"${args[@]}"`, which macOS
   `/bin/bash` 3.2 treats as unbound under `set -u`. Both calls now use
   `${args[@]+"${args[@]}"}`. A new regression test runs
   `/bin/bash scripts/validate --log`.
2. **Toolchain components** (the Codex thread at
   `apps/desktop/scripts/run:158`, also Copilot finding 1) (`b1adc72f`):
   - `check_pins` now checks that the `rust-toolchain.toml` components
     (rustfmt, clippy) are installed for the pinned toolchain.
   - `setup` always runs an idempotent `rustup component add`. It has to,
     because `rustup show active-toolchain` accepts an existing toolchain
     that lacks the components.
   - The modes matrix gains a `component_missing` case, making 7 cases.
3. **Linux prerequisites** (Copilot finding 2) (`b1adc72f`). The preflight
   now checks everything on the documented apt list: openssl,
   ayatana-appindicator3-0.1, librsvg-2.0, libxdo (via `xdo.h`), and cc,
   curl, wget and file. It still never runs sudo.
4. **Wheel dist-info guard** (Copilot finding 4) (`5fe9a55e`).
   `check_wheel_members` now requires exactly one `lrh-*.dist-info/`, with
   tests for zero and for two.
5. **`scripts/test` default output** (Copilot finding 3): dismissed.
   - The WI requires the `desktop: SKIPPED ...` line.
   - The existing "Testing lrh" and `[PASS]`/`[FAIL]` lines are unchanged,
     and the log-redirection tests still assert them.

Copilot's findings have no inline threads, so they were acknowledged in a PR
comment that cites the fix commits.

6. **CI regression from item 3 (`b4cf9608`).** On `45421d81` the required
   `tests` and `coverage` checks failed:
   - The new `xdo.h` check read the real `/usr/include`, and the stock
     ubuntu runner lacks libxdo-dev.
   - The stop-work condition fired again, and the user chose to fix it in
     this PR.
   - The fix:
     - The header path can now be overridden (`LRH_DESKTOP_XDO_HEADER`).
     - The test stubs cc, wget and file.
     - A new `LinuxPrerequisitesTest` stubs `uname`, so the Linux branch
       runs on any host.
   - The two low-severity items from the cold review are also fixed:
     - The failure matrix now asserts each case's exact error.
     - A test checks that `setup` runs `rustup component add`.

# Validation

- `scripts/format --desktop` and `scripts/lint --desktop` pass (black,
  pylint, pyright, cargo fmt --check, clippy -D warnings).
- `scripts/test --desktop` (after `b4cf9608`): 1838 Python tests OK and 4 Rust tests pass.
- `scripts/validate --log` passes under both the default bash and
  `/bin/bash` 3.2.
- `scripts/check-workflows`: OK.
- `apps/desktop/scripts/run setup` passes on the Mac, and reports rustfmt
  and clippy as up to date.

# Follow-up

Next: confirm-fixes, resolving the Codex thread, a substitute cold review of
the new HEAD, and a CI re-check that includes macOS.
