---
id: EV-LRH-CONSOLE-DESKTOP-PROTOCOL
title: "LRH desktop server protocol v1 validation"
type: validation_output
status: recorded
related_work_items:
  - WI-LRH-CONSOLE-DESKTOP-PROTOCOL
related_focus: []
source:
  kind: local_validation_run
  command: "PYTHONPATH=src python -m unittest tests.smoke.desktop_protocol_smoke -v"
  captured_at: 2026-09-25T21:27:00Z
  base_commit: fa837320e0a01598353dd2822216fc1cbd75d531
summary_result: pass_with_platform_limits
artifacts:
  - src/lrh/desktop_protocol.py
  - src/lrh/desktop_supervisor.py
  - docs/reference/desktop-server-protocol.md
  - tests/cli_tests/desktop_protocol_test.py
  - tests/cli_tests/desktop_supervisor_test.py
  - tests/smoke/desktop_protocol_smoke.py
metrics:
  unit_tests_total: 1770
  desktop_protocol_unit_tests: 42
  desktop_supervisor_unit_tests: 10
  desktop_protocol_smoke_tests: 20
  spawn_to_ready_median_seconds: 0.198
  shutdown_to_exit_median_seconds: 0.289
  stdin_close_to_exit_median_seconds: 0.285
blocked_actions:
  - "Linux and Windows behavior was not observed; this record does not claim either platform."
  - "The Tauri shell's own process boundary (spawn, pipe inheritance, Quit, crash) is not exercised here and must be validated by WI-LRH-CONSOLE-DESKTOP-L0 on macOS."
modified_actions:
  - "The minimal supervisor example is src/lrh/desktop_supervisor.py (python -m lrh.desktop_supervisor), added to the work item's artifact list with its hermetic test file."
approval_records: []
---

# LRH desktop server protocol v1 validation

This records what was observed while implementing
`WI-LRH-CONSOLE-DESKTOP-PROTOCOL`. The normative contract is
`docs/reference/desktop-server-protocol.md`. Everything below was run on the
feature branch built from `origin/main` at `fa837320`. Observed results are
kept separate from design expectations.

## Environment

| Item | Value |
| --- | --- |
| OS | macOS 26.6.2 (Darwin 25.6.0, arm64) |
| Python | 3.11.8 (conda-forge build) |
| Black / Ruff | 26.3.1 / 0.15.12 (repository pins) |
| LRH | editable install of this checkout (`lrh 0.2.5.dev2741+gfa837320e.d20260925`) |
| Agent / backend | Claude Code in the Claude desktop app (`claude_app`), model `claude-opus-5-5` |

The machine's shared conda environment had Black 25.11.0 and Ruff 0.15.0, and
its `lrh` was an editable install of a different worktree. To avoid validating
the wrong code or changing that shared environment, canonical validation ran
in an isolated session-scratch virtualenv. That venv was created with the
repository's canonical install (`pip install -e ".[dev]" -c constraints-dev.txt`)
and put first on `PATH`.

## Canonical validation (observed)

| Command | Result |
| --- | --- |
| `scripts/version tools` | Ruff 0.15.12, Black 26.3.1, Python 3.11.8; LRH CLI and metadata agree. |
| `scripts/format --check --diff` | 261 files unchanged. |
| `scripts/lint` | Ruff: all checks passed; Black clean; test guardrails passed (exit 0). |
| `scripts/test --log` | `Ran 1770 tests in 121.892s`, `OK`. |
| `lrh validate` | `Validation completed: 0 error(s), 0 warning(s)`. |
| `python -m unittest tests.smoke.desktop_protocol_smoke` | `Ran 20 tests in 11.917s`, `OK`. An earlier 17-test revision passed three consecutive reruns. The final desktop suites (72 tests) produced zero `ResourceWarning`s under `-W always::ResourceWarning`. |
| `scripts/smoke` | Run on the 17-test revision: 29 tests, 1 failure, in the pre-existing `prompt_cli_install_smoke` (see below). All desktop protocol smoke tests passed within that run. |

`scripts/smoke` failure, unrelated to this change: `prompt_cli_install_smoke`
installs the built wheel with `--no-deps` into a fresh venv and runs
`lrh --help`, which fails with `ModuleNotFoundError: No module named 'yaml'`. On
`origin/main`, `lrh.cli.main` already imports `lrh.control` (which imports
`yaml`) at module load, so the missing dependency predates this work. This
change adds no new third-party imports.

## Protocol behavior (observed on macOS)

Each row is an automated real-process smoke test unless marked "unit". Unit
tests run the same session code in-process over OS pipes with a real loopback
HTTP server.

| Behavior | Observed |
| --- | --- |
| Startup and endpoint discovery | `ready` reported `127.0.0.1`, an OS-assigned port, protocol 1, backend name, version, and Python version, and the resolved workspace. The reference supervisor verified it; `/health` returned 200 and `ping` round-tripped. |
| Channel separation | Raw stdout held only `ready`/`stopping`/`stopped` JSON lines; the human `ready` log was on stderr. A factory that printed to `sys.stdout` and wrote directly to descriptor 1 had both strings diverted to stderr. |
| Malformed input | `hello\n` produced one `failed` with `malformed_request`, then exit 3. Oversized input produced `message_too_large` (unit). |
| Incompatible protocol | `protocol_version: 2` produced `unsupported_protocol_version` with `supported_versions: [1]` and the correlated `launch_id`, then exit 3. |
| Control-directory workspace | Configuring `<repo>/project` produced a verified handshake whose `project_root` was `<repo>` and `project_dir` was `<repo>/project`. |
| Invalid workspace selection | A missing path gave `invalid_workspace`, and a non-LRH directory gave `workspace_not_lrh_project`, both exit 3. Relative paths and files were also rejected, and a subdirectory of a real project was refused rather than resolved upward (unit). |
| Startup failure | A bind failure gave `bind_failed`; a server failing its own status self-check gave `startup_self_check_failed` and closed its socket (unit). A wrong executable (exits silently) was reported by the supervisor as `exited_before_ready`. An executable printing non-protocol text gave `malformed_handshake`, and the owned child was terminated. |
| Hostile or broken peers | A 40 KB control `type` made of backslashes produced a bounded `error` (`unknown_message_type`, truncated echo); the server kept serving and later stopped normally. An unexpected exception after ready produced `stopping`/`stopped` with `internal_error` (exit 1), never `failed` (unit). A fake child that closed stdout but stayed alive was reported as `exited_before_ready` and terminated. A fake `ready` for another launch ID failed fast with `launch_id_mismatch`, and the child was terminated. |
| Timeouts | With no start request, the child sent `start_request_timeout` after `--desktop-start-timeout 0.5` and exited 3. For a child that never answers, the supervisor's 1 s startup deadline gave `startup_timeout`, and the owned child was terminated within the bound. |
| CLI compatibility | `--desktop-protocol --port 8765` (the default value, given explicitly) exited 2 with no stdout. An unrelated foreground `lrh serve --port 0` printed its usual `listening on` line and kept serving. |
| Graceful stop | `shutdown` produced `stopping` then `stopped` (`shutdown_requested`), exit 0, no escalation, and the port closed. SIGTERM gave reason `signal` and exit 0. |
| Parent-channel loss | Closing stdin gave `parent_channel_closed` and exit 4 with no escalation. SIGKILL of an intermediate parent that owned the pipes made the backend exit and its port close. SIGKILL of a parent while the stdin write end stayed open elsewhere made the backend exit via the parent-process watchdog. Both completed within the 7.25 s test bound. |
| Restart and stale events | `DesktopSupervisor.start()` twice returned the same handshake (one child). `restart()` observed exit 0 of the first child before the second launched with a new launch ID. A control message with an old launch ID got `launch_id_mismatch` and the server kept running (unit). |
| Isolation from an unrelated server | Across owned start/stop, a supervisor startup timeout, and a pipe-close stop, the unrelated foreground `lrh serve` process stayed running and answered `/health` 200. |
| Read-only boundary | In desktop mode `POST` returned 405 with `X-Frame-Options: DENY` and the existing CSP. `/shutdown` returned 404. `ready` fixes `read_only: true` and `execution_authority: false` (unit). |

### Measured latencies

Five runs each against this repository's own workspace, using the reference
supervisor and `python -m lrh.cli.main`:

| Interval | min | median | max |
| --- | --- | --- | --- |
| spawn → verified `ready` | 0.191 s | 0.198 s | 0.205 s |
| `shutdown` → process exit | 0.284 s | 0.289 s | 0.295 s |
| stdin close → process exit | 0.279 s | 0.285 s | 0.290 s |

## Independent pre-push review

A cold-context review subagent (`/lrh-self-review` diff-mode) reported six
findings. The top finding was re-verified directly: an oversized echoed
control `type` made the child send `failed` after `ready` and exit 1. All six
were fixed before the PR was opened:

1. Unbounded echoes could turn an error reply into an internal error after
   `ready`. Echoes are now truncated, and post-ready errors stop the server
   with `stopping`/`stopped`.
2. The reference supervisor could leave a child alive after
   `exited_before_ready`. Every failed start now escalates against the owned
   handle, and `DesktopSupervisor.start` stops a previous child before
   relaunching.
3. A mismatched `ready` was treated as stale and waited past. It now fails the
   launch.
4. A `project/` control-directory workspace was rejected by the reference
   supervisor's identity check. The check now uses the echoed request and
   `project_dir`.
5. The exit-code table misdescribed parent loss before `start`. The doc was
   corrected.
6. The doc now notes that existing Meta selector routes can show other
   registered projects, and that a blocked stdout write is bounded only by
   escalation.

## Supervisor example (observed)

```bash
python -m lrh.desktop_supervisor --lrh-executable "$(command -v lrh)" --project-root .
```

The example emitted `ready` (with URL, PID, backend, and workspace), then
`health` status 200, `ping` ok, and `stopped` with exit code 0, no escalation,
and reason `shutdown_requested`. With `--project-root /tmp` it emitted `failed`
with `backend_failed` / `workspace_not_lrh_project` (backend exit 3). With
`--lrh-executable /usr/bin/true` it emitted `failed` with `exited_before_ready`.

## Design expectations not observed here

- Linux is expected to match macOS, since it uses the same POSIX pipes,
  signals, and reparenting, but nothing ran on Linux for this record.
- On Windows only stdin EOF can detect parent loss, because the parent PID does
  not change when the parent exits; SIGHUP is absent. This is untested.
- Pipe-inheritance safety for the real shell depends on how Tauri/Rust spawns
  the child. The contract documents the requirement, and L0 must demonstrate it
  on macOS: Quit, app crash, and Dock reopen.
- The backend does not validate the HTTP `Host` header (unchanged from
  foreground Serve). Navigation and capability limits belong to the L0 shell.
