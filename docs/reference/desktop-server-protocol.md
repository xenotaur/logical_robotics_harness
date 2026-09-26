# LRH desktop server protocol (version 1)

This page is the normative contract between a desktop supervisor (the planned
LRH Console Tauri shell, `WI-LRH-CONSOLE-DESKTOP-L0`) and the Python
`lrh serve` backend it owns. It covers launch, the ready/failed handshake,
control messages, graceful shutdown, parent-loss cleanup, deadlines, and the
supervisor's restart and ownership rules.

Implementation: `src/lrh/desktop_protocol.py` (child side) and
`src/lrh/desktop_supervisor.py` (a minimal Python reference supervisor). Ordinary
`lrh serve` without `--desktop-protocol` is unchanged.

## Summary

| Topic | Rule |
| --- | --- |
| Entry point | `<lrh-executable> serve --desktop-protocol [--desktop-start-timeout SECONDS]` |
| Transport | The child's own stdin (parent → child) and stdout (child → parent) pipes, held privately by the parent. |
| Framing | One UTF-8 JSON object per line (NDJSON), `\n`-terminated, at most 65,536 bytes including the newline. |
| Human logs | stderr only. Machine messages never appear on stderr; human text never appears on stdout. |
| Protocol id | `"protocol": "lrh-desktop-server"`, `"protocol_version": 1`. |
| Bind | Always `127.0.0.1`, OS-assigned port (`port 0`). The actual port is reported in `ready`. |
| Workspace | Explicit absolute path in the `start` request; no fallback. The effective identity is echoed. |
| Ownership | The child handle and its pipes. A launch ID only correlates messages; it is not a secret. |
| Parent loss | stdin EOF, or (POSIX) the parent process changing, stops the server and exits. |
| Authority | `ready` means reachable. It never means the project validates or that work may execute. |

## Launching the backend

The supervisor runs one explicitly configured executable, never a name looked
up through an interactive shell, and appends exactly these arguments:

```bash
/absolute/path/to/lrh serve --desktop-protocol
```

`python -m lrh.cli.main serve --desktop-protocol` is equivalent when the
supervisor is configured with a Python interpreter instead of the `lrh` script.

- `--desktop-protocol` cannot be combined with `--host`, `--port`,
  `--project-root`, `--codex-archive-root`, `--allow-nonlocal-host`, or
  `--show-config`, even when their values equal the defaults. The child exits
  with code 2 and a usage message on stderr, before any machine message.
- `--desktop-start-timeout SECONDS` (0.1–120, default 10) bounds how long the
  child waits for the `start` request. It is only valid with `--desktop-protocol`.
- Configure the real executable. A wrapper that spawns `lrh` as a grandchild
  (for example `conda run`) breaks the pipe and process-handle ownership this
  contract relies on unless it `exec`s. The reported `pid` shows which process
  actually serves.

Spawn the child with stdin and stdout as new pipes and stderr as a pipe the
supervisor drains (or a private log file). Do not let other processes inherit
the write end of the child's stdin; see [Parent loss](#parent-loss).

## Framing

- Each message is a single JSON object encoded as UTF-8 on one line, followed by
  `\n`. The child also accepts `\r\n` and ignores blank lines.
- A message may not exceed 65,536 bytes including the newline. Oversized or
  unparseable input before `ready` produces `failed`; after `ready` it produces
  an `error` event and a fatal stop (see [Control messages](#control-messages)).
- The child writes each message with one flushed write to a reserved copy of
  the original stdout descriptor. In desktop mode, descriptor 1 and `sys.stdout`
  are redirected to stderr, so stray prints or library output land in human
  diagnostics instead of corrupting the channel.
- Receivers must ignore unknown fields. A sender must bump `protocol_version`
  for any change whose omission or misunderstanding would change safety or
  identity semantics; additive informational fields do not require a bump.

Every message carries this envelope:

| Field | Type | Meaning |
| --- | --- | --- |
| `protocol` | string | Always `"lrh-desktop-server"`. |
| `protocol_version` | integer | `1` for this document. |
| `type` | string | Message type (below). |
| `launch_id` | string or null | Correlation ID from `start`; `null` only in failures before a valid `start` could be read. |

## Version compatibility

Version negotiation is a single exact match. The parent names the one version
it speaks in `start`. The child supports the set `[1]`; any other value (including
JSON booleans) fails with `unsupported_protocol_version`, and
`error.details.supported_versions` lists what the child accepts. A supervisor
that sees `unsupported_protocol_version`, a wrong `protocol` name, or a `ready`
it cannot verify must show an incompatible-backend state rather than retry.

Control messages after `ready` must repeat the negotiated `protocol_version`.
The backend's own package version is informational (`backend.version`) and is
never used for compatibility decisions; it may be `null` when package metadata
is unavailable.

## Startup

### `start` (parent → child, first message)

```json
{"protocol":"lrh-desktop-server","protocol_version":1,"type":"start","launch_id":"6f1c…","workspace":{"project_root":"/Users/me/src/lrh"}}
```

| Field | Rule |
| --- | --- |
| `launch_id` | Required; 1–128 characters from `A-Z a-z 0-9 . _ : -`. Use a fresh random value (for example a UUID) per launch. |
| `workspace.project_root` | Required absolute path, at most 4,096 UTF-8 bytes, to an LRH repository root (containing `project/focus` and `project/work_items`) or to the `project/` control directory itself. |

Workspace resolution is strict. The path must be absolute, exist, and be a
directory that directly contains the LRH control directory. There is no
parent-directory search, no current-directory default, and no Meta registry
lookup, so a subdirectory of a project is rejected rather than silently
serving its enclosing project.

### `ready` (child → parent)

The child sends `ready` only after it has validated the request and bound
`127.0.0.1` on an OS-assigned port, started serving, and fetched its own
`/api/status` route successfully. That route must identify `lrh serve` on the
bound port.

```json
{"protocol":"lrh-desktop-server","protocol_version":1,"type":"ready","launch_id":"6f1c…",
 "backend":{"name":"lrh","version":"0.2.5","python":"3.11.8"},"pid":4242,
 "workspace":{"requested_project_root":"/Users/me/src/lrh","project_root":"/Users/me/src/lrh",
              "project_dir":"/Users/me/src/lrh/project","name":"lrh"},
 "endpoint":{"scheme":"http","host":"127.0.0.1","port":50543,"url":"http://127.0.0.1:50543/"},
 "read_only":true,"execution_authority":false}
```

`workspace.project_root` is the fully resolved (symlink-free) repository root
that Serve uses; `workspace.project_dir` is its control directory. Values echoed
from the request into error replies are truncated, so no reply approaches the
size limit. `read_only: true` and `execution_authority: false` are fixed in
version 1.

The supervisor must accept `ready` only if **all** of these hold, and otherwise
stop the child and report an incompatible or mismatched backend:

1. `protocol` matches, and `protocol_version` is a supported JSON integer.
   A JSON `true` is not version 1.
2. `launch_id` equals the one it sent for the current launch.
3. `workspace.requested_project_root` equals exactly the path it sent, and the
   reported root and control directory agree with the canonical (`realpath`)
   form of that path:
   - For a repository root, `workspace.project_root` equals it and
     `workspace.project_dir` is `<root>/project` (or the root itself for a
     bare control directory).
   - For a `project/` control directory, `workspace.project_dir` equals it
     and `workspace.project_root` is its parent.
4. `endpoint.host` is a loopback address and `endpoint.port` is 1–65535.

Only then may it load `endpoint.url`. A responding port, a matching process
name, or a successful HTTP response is never proof that a server is this
launch's child.

### `failed` (child → parent)

```json
{"protocol":"lrh-desktop-server","protocol_version":1,"type":"failed","launch_id":"6f1c…",
 "backend":{"name":"lrh","version":"0.2.5","python":"3.11.8"},
 "error":{"code":"workspace_not_lrh_project","message":"…","details":{"requested_project_root":"/tmp"}}}
```

After `failed` the child writes nothing more and exits: code 3, or 4 for
`parent_channel_closed`, or 1 for `internal_error`. It never sends both
`ready` and `failed`.

| `error.code` | Cause | Supervisor action |
| --- | --- | --- |
| `malformed_request` | First line not valid JSON object, wrong `type`, missing/invalid `workspace`. | Bug in the supervisor; show failed. |
| `message_too_large` | First message exceeds 65,536 bytes. | Bug in the supervisor; show failed. |
| `unsupported_protocol` | `protocol` is not `lrh-desktop-server`. | Show incompatible. |
| `unsupported_protocol_version` | Version not in `details.supported_versions`. | Show incompatible. |
| `invalid_launch_id` | Launch ID missing or outside the allowed alphabet/length. | Bug in the supervisor. |
| `invalid_workspace` | Path relative, missing, not a directory, or over 4,096 bytes. | Ask the user to fix Settings. |
| `workspace_not_lrh_project` | Directory has no LRH control directory. | Ask the user to fix Settings. |
| `bind_failed` | Loopback bind failed or bound a non-loopback address. | Show failed; offer retry. |
| `startup_self_check_failed` | Server did not answer its own status route correctly. | Show failed; offer retry. |
| `start_request_timeout` | No `start` within `--desktop-start-timeout`. | Supervisor was too slow or wrote nothing. |
| `startup_cancelled` | SIGTERM/SIGINT/SIGHUP or parent exit before `start` arrived. | Expected during cancellation. |
| `parent_channel_closed` | stdin closed before `start`. | Expected during cancellation. |
| `internal_error` | Unexpected backend exception before `ready` (details on stderr). | Show failed with stderr tail. |

## Control messages

After `ready`, the parent may send these messages. Each must carry the
envelope with the current `launch_id` and may include an optional `request_id`
string (at most 128 characters) that the child echoes in its reply.

| Parent sends | Child replies | Effect |
| --- | --- | --- |
| `{"type":"shutdown",…}` | `stopping`, then `stopped`, then exit 0 | Graceful stop. |
| `{"type":"ping","request_id":"r1",…}` | `{"type":"pong","request_id":"r1",…}` | Channel liveness check. |
| any message with a different `launch_id` | `error` `launch_id_mismatch` | Ignored; server keeps running. |
| wrong `protocol` / `protocol_version` | `error` `unsupported_protocol` / `unsupported_protocol_version` | Ignored; server keeps running. |
| a second `start` | `error` `already_started` | Ignored. |
| an unknown `type` | `error` `unknown_message_type` with `details.supported_types` | Ignored. |
| invalid JSON / oversized line | `error` `malformed_message` / `message_too_large`, then `stopping`/`stopped` with reason `protocol_error`, exit 5 | Fatal: framing can no longer be trusted. |

`stopping` and `stopped` carry `reason`:

| `reason` | Trigger | Exit code |
| --- | --- | --- |
| `shutdown_requested` | `shutdown` message. | 0 |
| `signal` | SIGTERM, SIGINT, or SIGHUP delivered to the child. | 0 |
| `parent_channel_closed` | EOF on stdin, or stdout became unwritable. | 4 |
| `parent_process_exited` | (POSIX) the child's parent process changed. | 4 |
| `protocol_error` | Malformed or oversized control input. | 5 |
| `internal_error` | Unexpected backend exception after `ready` (details on stderr). | 1 |

After `ready`, the only terminal messages are `stopping` and `stopped`; the
child never sends `failed` once it has sent `ready`.

There is deliberately **no HTTP shutdown route**: the only stop controls are
the private pipe, signals delivered through the owned child handle, and pipe
closure. The HTTP surface keeps rejecting non-GET/HEAD methods with 405.

## Parent loss

The child treats the loss of its supervising parent as a stop condition:

- **stdin EOF** (primary, all platforms). When the parent process exits for any
  reason, the operating system closes its pipe ends and the child reads EOF.
  This works only if no other process inherited the write end of the child's
  stdin. Rust's `std::process::Command` and Python's `subprocess` (with
  `close_fds=True`) do not leak it; the shell must not pass that descriptor to
  other children it spawns.
- **Parent process watchdog** (secondary, POSIX). The child records
  `getppid()` at startup and stops if it changes (an orphan is reparented). This
  covers a leaked stdin write end. On Windows the parent PID does not change
  when the parent exits, so only EOF applies there.
- **stdout write failure**: a failed write marks the channel broken and stops.

The child checks these conditions every 0.25 seconds, then stops its HTTP
server with a 5-second bound and exits.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Graceful stop (`shutdown_requested` or `signal`). |
| 1 | Unexpected internal error: `failed` (`internal_error`) before ready, or `stopping`/`stopped` with reason `internal_error` after ready. |
| 2 | CLI usage error; no machine message was written. |
| 3 | Startup failed; exactly one `failed` message was written. This includes `startup_cancelled`, where the parent process exited or a signal arrived before `start`. |
| 4 | Parent channel closed before `start` (`failed` `parent_channel_closed`), or parent lost after ready (`parent_channel_closed` / `parent_process_exited`). |
| 5 | Fatal protocol error after ready. |
| other / signal | The supervisor escalated (terminate/kill) or the process crashed. |

## Deadlines

Child-side (implemented in `lrh.desktop_protocol`):

| Deadline | Value |
| --- | --- |
| Wait for `start` | 10 s default (`--desktop-start-timeout`, 0.1–120 s) |
| Readiness self-check | 5 s |
| Stop-condition polling interval | 0.25 s |
| HTTP server stop | 5 s, then exit regardless |

Parent-side (required of the supervisor; defaults in `lrh.desktop_supervisor`):

| Deadline | Default | On expiry |
| --- | --- | --- |
| Spawn → `ready`/`failed` | 20 s | Treat as `startup_timeout`; escalate against the owned child. |
| `shutdown` → process exit | 10 s | Terminate the owned child handle. |
| Terminate → process exit | 5 s | Kill the owned child handle, then wait for exit. |

The 20-second startup budget covers interpreter start and imports on a cold
disk. On the tested Mac (Apple silicon) spawn-to-ready took about 0.2 seconds.

## Supervisor responsibilities

These rules are what the L0 shell must implement. `lrh.desktop_supervisor`
implements them in Python.

**State machine.** Track one supervised server with states `stopped`,
`starting`, `running`, `stopping`, and `failed`. "Setup required" and
"incompatible" are UI conditions derived from `failed` codes, not fake ready states.

**Serialization.** Process Start, Stop, Restart, and Quit through one queue or
lock. Start while `starting` or `running` is a no-op that returns the current
state (idempotent). Never run two owned children at once.

**Restart ordering.** Restart means: send `shutdown`, wait for the *current
child handle* to exit (escalating per the deadlines above), revoke the old
endpoint origin, then spawn a new child with a **new** launch ID. Never spawn
before the previous child's exit has been observed.

**Stale events.** Bind each reader to the child handle it was created for, and
compare every message's `launch_id` with the current launch. Discard (and log)
messages from a previous launch or previous handle, and never let them change
the current state or endpoint. During startup, a `ready` or `failed` from the
current handle whose `launch_id` does not match is a failed launch
(`launch_id_mismatch`): stop that child rather than waiting past it.

**Exit handling.** Always wait on the child handle, and check it before
treating a server as running: Start must not return a previous handshake for
a child that has already exited. An exit while `running` is
an unexpected stop: show failed with the exit code and a bounded stderr tail
(the reference keeps 64 KiB). An exit while `stopping` completes the stop. An
exit before `ready` is a startup failure, whether or not `failed` was received.

**Ownership and escalation.** Only ever signal, terminate, or kill the process
handle this supervisor spawned. Never look up or stop processes by name, port,
PID file, or HTTP response. Never adopt an already-running server as owned.

**Quit and crash.** On Quit, run the normal stop sequence with its bounds. If
the shell itself crashes, the operating system closes the pipes and the child
exits on EOF (or the POSIX watchdog); no cleanup action is needed from a later
app launch, and a later launch must not try to find the old child.

**Failed starts.** Any startup failure must leave no running child: close
stdin, and if the child has not exited, escalate against its handle before
reporting the failure. A child that closes stdout but keeps running is a
startup failure, not a stopped server.

**Diagnostics.** Drain stdout and stderr continuously. If the supervisor stops
reading stdout, the child's next protocol write can block. Neither signals nor
stdin closure can interrupt that write, so only the terminate/kill escalation
bounds it. Keep only a bounded stderr tail. It may contain local paths; do not upload it or put it
in URLs.

## Security boundary

- The loopback-only bind and every existing HTTP protection are unchanged in
  desktop mode: read-only routes, 405 for mutating methods, `X-Frame-Options: DENY`,
  and the restrictive `Content-Security-Policy`.
- The launch ID correlates messages and rejects stale ones. It is not an
  authentication token and grants nothing over HTTP.
- `ready` means the viewer is reachable. It does not mean the project validates,
  that any work item is ready, or that any execution is authorized.
- The workspace is fixed at startup, but existing Serve Meta routes still
  display other projects registered in the local Meta workspace when asked
  with a project selector, as they do in foreground mode. That is Serve's
  existing read-only Meta view, not a fallback of the served root.
- The backend does not check the HTTP `Host` header, so another local process
  or a browser page on the same machine can reach the loopback port, exactly
  as with foreground `lrh serve`. The L0 shell's navigation and capability
  policy, and any future Host/Origin validation, are separate work.

## Design choices

- **stdio pipes rather than a socket, port file, or HTTP control route.** The
  pipes exist only between parent and child, need no discovery, close
  automatically when either side dies, and are what Tauri's process API
  provides. A control socket or port file would need its own authentication.
  An HTTP control route would be reachable by any local process.
- **Start request on stdin rather than in CLI arguments.** It gives one
  versioned, size-bounded structure with testable validation. It also keeps the
  launch ID and workspace out of process listings, and leaves room for additive
  fields.
- **A single exact version** instead of range negotiation. Version 1 has one
  consumer. Newer versions can add a supported-versions list without breaking
  the envelope.
- **Fail closed on framing errors after ready.** Only the owning parent writes
  to the pipe, so garbage means a broken supervisor, and resynchronizing would
  only guess.
- **Self-check before ready.** Binding alone does not prove routing works. One
  local GET of `/api/status` does, at negligible cost.
- **Standard library only.** No server framework or new dependency; the
  existing `ThreadingHTTPServer` is reused.

## Exercising the contract without Tauri

Run the reference supervisor. It starts an owned child, verifies the
handshake, checks `/health` and `ping`, and stops it:

```bash
python -m lrh.desktop_supervisor --lrh-executable "$(command -v lrh)" --project-root .
```

To browse the served page before it stops, add `--hold 60`, then open the
printed `url`. To test a source checkout without installing it, put `src` on
`PYTHONPATH` and supervise the current interpreter:

```bash
PYTHONPATH=src python -m lrh.desktop_supervisor --use-current-python --project-root .
```

Drive the raw protocol by hand:

```bash
printf '%s\n' \
  '{"protocol":"lrh-desktop-server","protocol_version":1,"type":"start","launch_id":"manual-1","workspace":{"project_root":"'"$PWD"'"}}' \
  '{"protocol":"lrh-desktop-server","protocol_version":1,"type":"ping","launch_id":"manual-1","request_id":"r1"}' \
  '{"protocol":"lrh-desktop-server","protocol_version":1,"type":"shutdown","launch_id":"manual-1"}' \
  | lrh serve --desktop-protocol
```

Expected stdout: `ready`, `pong`, `stopping`, `stopped`, with exit code 0. The
human log line goes to stderr.

Automated coverage:

```bash
scripts/test tests/cli_tests/desktop_protocol_test.py
scripts/test tests/cli_tests/desktop_supervisor_test.py
PYTHONPATH=src python -m unittest tests.smoke.desktop_protocol_smoke -v
```

The smoke suite (also run by `scripts/smoke`) starts real child processes with
bounded waits. It covers startup and endpoint discovery, stdout/stderr
separation, malformed and unsupported input, invalid workspaces, CLI conflicts,
child and supervisor timeouts, and wrong executables. It also covers graceful
stop, SIGTERM, pipe close, a killed parent with and without a leaked stdin, and
restart ordering, and it checks that an unrelated foreground `lrh serve` stays
untouched.

## Platform status

Version 1 behavior was observed on macOS (Darwin, Python 3.11) through the
tests above. See `project/evidence/EV-LRH-CONSOLE-DESKTOP-PROTOCOL.md`. Linux
is expected to behave the same (POSIX pipes, signals, reparenting), but this
item did not observe it. On Windows, signals other than termination are not
available, SIGHUP does not exist, and the parent-PID watchdog cannot detect
parent exit, so stdin EOF is the only parent-loss signal there; it is untested.
The Tauri shell must re-validate its own process boundary on each platform it
claims.

## Related

- [`lrh serve` CLI reference](cli/serve.md)
- Design: `project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md`
- Consumer: `project/work_items/proposed/WI-LRH-CONSOLE-DESKTOP-L0.md`
