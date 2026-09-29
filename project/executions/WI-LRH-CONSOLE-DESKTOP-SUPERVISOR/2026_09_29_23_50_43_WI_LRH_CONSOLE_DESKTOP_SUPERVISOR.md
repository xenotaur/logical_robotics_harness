---
execution_id: 2026_09_29_23_50_43_WI_LRH_CONSOLE_DESKTOP_SUPERVISOR
prompt_id: PROMPT(WI-LRH-CONSOLE-DESKTOP-SUPERVISOR:WI_LRH_CONSOLE_DESKTOP_SUPERVISOR)[2026-09-29T23:27:13+00:00]
work_item: WI-LRH-CONSOLE-DESKTOP-SUPERVISOR
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/758
commit: 
agent: "claude_app"
instruction_source: "project/work_items/proposed/WI-LRH-CONSOLE-DESKTOP-SUPERVISOR.md"
session_transcript: pending
created_at: 2026-09-29T23:50:43+00:00
---

# Summary

This record covers the implementation of `WI-LRH-CONSOLE-DESKTOP-SUPERVISOR`.
The run was a human-initiated `/lrh-execute WS-LRH-CONSOLE-LOCAL-DOGFOOD`, which
resolved to this work item as the first ready one in the workstream's list
order. `/lrh-implement` ran inline, and `/lrh-land` follows.

- The branch `xenotaur/feat/wi-lrh-console-desktop-supervisor` was cut from
  `origin/main` `55484772`.
- The chain gate approved the stored default conditions:
  - Completion: "PR merged, its execution records landed, and any linked work
    item resolved."
  - Stop-work: "Any failing CI check, a reviewer finding that isn't
    Clear-satisfied on re-verification, or an ambiguous/refused
    merge-authorization reply."

# Result

`66a94431` adds the owned-backend Rust supervisor for desktop-server-protocol
v1, with no UI.

**`apps/desktop/src-tauri/src/supervisor.rs`**

- **`OwnedServer`** handles one launch:
  - It spawns an explicit program and keeps its pipes private.
  - It sends `start` with a fresh launch ID.
  - It accepts only a verified `ready`. That means a matching protocol name,
    an integer version, the same launch ID, the echoed and canonical
    workspace, and a loopback endpoint.
- **Output:** it drains stdout and stderr continuously, keeps a bounded 64 KiB
  stderr tail, and discards messages from other launches.
- **Deadlines:** 20 s from spawn to ready. After a shutdown request, 10 s
  before SIGTERM, then 5 s before a kill.
- **Escalation** targets only the owned, unreaped child. It uses
  `libc::kill(SIGTERM)` on Unix, then kills and waits.
- **`Supervisor`** serializes Start, Stop and Restart:
  - Start is idempotent, even when called concurrently.
  - Restart waits for the old child to exit.
  - `generation` and `is_current()` reject stale callbacks.
  - `status()` can be read without blocking on a running operation.
  - A crash while running is reported as `Failed`.
- **`Drop` safety net:** dropping a server never leaves its child running.

**`apps/desktop/src-tauri/tests/supervisor_test.rs`** has 15 integration tests.
They run against a real `lrh serve --desktop-protocol` from `src/`, plus Python
fakes for the failure paths. They cover every case the work item lists,
including:

- parent loss, where the test binary re-execs itself as a supervisor and is
  SIGKILLed;
- a separately started `lrh serve` that stays untouched through Start,
  Restart, Stop and a failure.

**Supporting changes**

- `apps/desktop/scripts/run test` exports an explicit absolute
  `LRH_DESKTOP_TEST_PYTHON`.
- `Cargo.toml`: `serde_json` becomes a regular dependency, and `libc` is added
  as `=0.2.189` on Unix only.
- `lib.rs`: the stale L0 pointer is repointed (deferred from PR #757).
- `desktop-toolchain.md`: documents the tier-1 supervisor tests.

**Pre-push self-review** (`_SELFREVIEW`, `2026_09_29_23_49_16`). It found one
blocking bug: a failed start could SIGTERM a child that had died by signal and
was already reaped. `b515a228` fixes it and 4 should-fix items, with two
regression tests.

# Validation

All on macOS:

- `scripts/format --check --diff --desktop`: pass.
- `scripts/lint --desktop`: pass (black, pylint, pyright, cargo fmt --check,
  clippy `-D warnings`).
- `scripts/test --desktop`: the Python suite passes, plus 12 Rust unit tests
  and 15 supervisor integration tests. The integration tests passed three
  consecutive runs, taking about 2 s each and leaving no stray processes.
- Plain `scripts/test`: prints `desktop: SKIPPED (not requested; run
  scripts/test --desktop)`.
- `lrh validate`: 0 errors, 0 warnings.
- `scripts/check-workflows`: OK.

Linux will be checked by the `desktop (ubuntu-latest)` job on this PR.

# Follow-up

- `WI-LRH-CONSOLE-DESKTOP-SHELL` wires this supervisor to menus, Settings, and
  recovery pages.
- Windows parent loss (stdin EOF only) remains untested, as the protocol
  reference already notes.
