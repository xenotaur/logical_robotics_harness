---
execution_id: 2026_09_25_21_28_56_WI_LRH_CONSOLE_DESKTOP_PROTOCOL
prompt_id: PROMPT(WI-LRH-CONSOLE-DESKTOP-PROTOCOL:WI_LRH_CONSOLE_DESKTOP_PROTOCOL)[2026-09-25T19:56:52+00:00]
work_item: WI-LRH-CONSOLE-DESKTOP-PROTOCOL
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/727
commit: d9f0e49e722a2b940ac62fe8e943a2c814e9315a
created_at: 2026-09-25T21:28:56+00:00
agent: "claude_app"
instruction_source: "project/work_items/proposed/WI-LRH-CONSOLE-DESKTOP-PROTOCOL.md"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

Implement `WI-LRH-CONSOLE-DESKTOP-PROTOCOL` through a human-initiated
`/lrh-execute` chain: `/lrh-implement` inline, then `/lrh-land`. The goal is a
versioned machine interface that lets a desktop supervisor launch, identify,
monitor, and stop its own `lrh serve` process. Workstream:
`WS-LRH-CONSOLE-LOCAL-DOGFOOD`. Branch
`xenotaur/feat/wi-lrh-console-desktop-protocol` was cut from `origin/main` at
`fa837320`.

The chain gate approved the run plan and these conditions:

- Completion condition: "PR merged, its execution records landed, and any
  linked work item resolved."
- Stop-work condition: "Any failing CI check, a reviewer finding that isn't
  Clear-satisfied on re-verification, or an ambiguous/refused
  merge-authorization reply."

# Result

- Added `src/lrh/desktop_protocol.py` (child side) and the explicit
  `lrh serve --desktop-protocol` entry point in `src/lrh/serve.py`. It uses
  stdio NDJSON with a 64 KiB limit and separates human logs onto stderr.
- Ready/failed handshake:
  - the start request carries a strictly resolved explicit workspace;
  - the child binds `127.0.0.1` on an OS-assigned port and runs a
    self-check before sending `ready`;
  - `ready` reports versions, launch ID, and the actual endpoint.
- Control and lifecycle:
  - `ping` and `shutdown`;
  - stale launch IDs are rejected;
  - the child exits on parent-channel EOF or on POSIX reparenting;
  - SIGTERM stops it gracefully;
  - startup and stop deadlines are bounded.
- Foreground `lrh serve` and its HTTP protections are unchanged.
- Added `src/lrh/desktop_supervisor.py` as the minimal reference
  supervisor, runnable as `python -m lrh.desktop_supervisor`. The WI's
  artifact list and body were updated together to include it and its test
  file.
- Added `docs/reference/desktop-server-protocol.md`, which covers:
  - framing and versioning;
  - message and error-code tables, exit codes, and deadlines;
  - restart ordering and stale-event rules;
  - parent/child responsibilities and escalation;
  - the security boundary and design tradeoffs;
  - exact commands.

  It is linked from the reference index and `cli/serve.md`.
- Evidence: `project/evidence/EV-LRH-CONSOLE-DESKTOP-PROTOCOL.md`.
- Prior-art check: present in the WI; no warnings.
- The pre-push self-review (`_SELFREVIEW` record) found six issues. All six
  were fixed with regression tests before the PR was opened.

# Validation

Validation used macOS 26.6.2 (arm64), Python 3.11.8, and an isolated
session-scratch venv with the pinned Black 26.3.1 / Ruff 0.15.12. The shared
conda env's tools were mismatched, and its `lrh` pointed at another worktree.

- `scripts/version tools`: pins match.
- `scripts/format --check --diff`: 261 files unchanged.
- `scripts/lint`: exit 0.
- `scripts/test --log`: `Ran 1770 tests`, OK.
- `lrh validate`: 0 errors, 0 warnings.
- `python -m unittest tests.smoke.desktop_protocol_smoke`: 20 tests OK.
  Desktop unit suites: 42 + 10 tests OK. No `ResourceWarning`s.
- `python -m lrh.desktop_supervisor --lrh-executable "$(command -v lrh)" --project-root .`:
  - ready, health 200, ping ok, stopped with exit 0 and no escalation;
  - failure paths behaved as documented (`/tmp` workspace, `/usr/bin/true`).
- `scripts/smoke`: one failure, in `prompt_cli_install_smoke`, which predates
  this change and is unrelated to it. A `--no-deps` wheel install lacks `yaml`.

# Follow-up

- `WI-LRH-CONSOLE-DESKTOP-L0` consumes this contract. It must prove the
  Tauri/Rust process boundary on macOS: pipe inheritance, Quit, crash, and
  Dock reopen.
- Linux and Windows behavior is unobserved.
- Host/Origin validation and navigation limits belong to the shell or later
  work.
- The pre-existing `prompt_cli_install_smoke` `--no-deps` failure is not
  addressed here.
