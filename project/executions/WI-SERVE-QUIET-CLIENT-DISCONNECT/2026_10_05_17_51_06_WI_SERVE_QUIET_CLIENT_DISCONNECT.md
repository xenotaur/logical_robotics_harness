---
execution_id: 2026_10_05_17_51_06_WI_SERVE_QUIET_CLIENT_DISCONNECT
prompt_id: PROMPT(WI-SERVE-QUIET-CLIENT-DISCONNECT:WI_SERVE_QUIET_CLIENT_DISCONNECT)[2026-10-05T17:12:38+00:00]
work_item: WI-SERVE-QUIET-CLIENT-DISCONNECT
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/767
commit: 
agent: "claude_app"
instruction_source: "project/work_items/proposed/WI-SERVE-QUIET-CLIENT-DISCONNECT.md"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-10-05T17:51:06+00:00
---

# Summary

This record covers implementing `WI-SERVE-QUIET-CLIENT-DISCONNECT` (defect
D5 from the LRH Console L0 dogfood) through `/lrh-execute
WS-LRH-CONSOLE-LOCAL-DOGFOOD`, with `/lrh-implement` inline. The owner
approved the run plan at the chain gate.

# Result

**The fix.** `ThreadingHTTPServer.handle_error` in `src/lrh/serve.py` now
returns silently for client disconnects (`_CLIENT_DISCONNECT_ERRORS`:
`BrokenPipeError`, `ConnectionResetError`, `ConnectionAbortedError`). It
passes every other exception to `socketserver.BaseServer.handle_error`,
which still prints a traceback.

**Why at the server and not in each writer.** One override covers every
write path: `_write_json`, `_write_text`, `_write_download`, and
`BaseHTTPRequestHandler`'s own error responses. `ThreadingIPv6HTTPServer`
inherits it, and desktop-protocol mode builds the same server through
`_desktop_server_factory`.

**Code reading.** Every handler `except (FileNotFoundError, OSError,
ValueError)` block wraps only `render_*` calls, never a response write. So
a disconnect cannot be turned into a misleading 404.

**Divergence from the approved plan.** The plan named `BrokenPipeError` and
`ConnectionResetError`. Following a self-review nit, `ConnectionAbortedError`
was added: it is the Windows and occasional `ECONNABORTED` form of the same
client disconnect. The intent and file set are unchanged.

**Tests** (`tests/cli_tests/serve_test.py`, `TestServeClientDisconnect`):

- `test_mid_response_disconnect_is_quiet_and_server_keeps_serving` runs for
  both the foreground and desktop servers. A gated, patched
  `project_viewer_payload` waits until the client has closed with
  `SO_LINGER` 0, then returns an 8 MB body. The test asserts that exactly one
  disconnect-type exception reached `handle_error`, that stderr has no
  traceback, and that `/health` returns 200.
- `test_other_request_errors_are_still_reported`: a `RuntimeError` reaches
  the default handler, and its traceback is printed.
- With `src/lrh/serve.py` reverted, the disconnect test failed in both modes.
  It reproduced the owner's session 0.2 traceback, going through `do_GET` →
  `_write_json` to `BrokenPipeError: [Errno 32] Broken pipe`.

# Validation

- `scripts/format --check --diff` and `scripts/lint` passed. Both used the
  `LrhLocalAgent` env's pinned tools, with `PYTHONPATH` set to this worktree.
- `scripts/test --log`: `Ran 1909 tests`, `OK`.
- `TestServeClientDisconnect` passed 5 consecutive local reruns, and 3 more
  in review.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

None.
