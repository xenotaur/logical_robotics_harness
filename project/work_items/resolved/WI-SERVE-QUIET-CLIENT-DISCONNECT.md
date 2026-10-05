---
id: "WI-SERVE-QUIET-CLIENT-DISCONNECT"
title: "Stop Serve printing tracebacks when a client disconnects mid-response"
type: "deliverable"
status: "resolved"
blocked: false
blocked_reason: null
resolution: 'Implemented and merged in PR #767 (commit 23e9a233). ThreadingHTTPServer.handle_error now drops client disconnects (BrokenPipeError, ConnectionResetError, ConnectionAbortedError) with no traceback, and reports every other request exception as before. This covers foreground, IPv6, and desktop-protocol servers. Real-socket regression tests reproduce the owner traceback without the fix and pass with it.'
owner: "anthony"
contributors:
- "anthony"
assigned_agents: []
parent_id: "WS-LRH-CONSOLE-LOCAL-DOGFOOD"
related_focus: []
related_roadmap: []
related_workstreams:
- "WS-LRH-CONSOLE-LOCAL-DOGFOOD"
related_design:
- "project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md"
depends_on:
- "WI-LRH-CONSOLE-DESKTOP-DOGFOOD"
blocked_by: []
expected_actions:
- "edit_file"
- "create_file"
- "run_tests"
- "create_pr"
forbidden_actions:
- "force_push"
- "delete_branch"
- "merge_pr"
- "publish_package"
- "deploy_remote_service"
acceptance:
- "When a client closes the connection before Serve finishes writing a response (BrokenPipeError or ConnectionResetError), Serve logs no traceback and keeps serving later requests."
- "Other exceptions in a request handler are still reported as they are today."
- "A regression test drives a real loopback request that disconnects mid-response and asserts there is no traceback output and the server stays healthy."
- "Foreground lrh serve and --desktop-protocol mode both behave this way."
required_evidence:
- "test_output"
- "lrh_validate"
artifacts_expected:
- "src/lrh/serve.py"
- "tests/cli_tests/ (a regression test for client disconnects)"
---

# Quiet client disconnects in Serve

## Summary

When a browser or the LRH Console webview leaves a page while Serve is still
writing the response, Serve prints a full `BrokenPipeError` traceback. The
disconnect is harmless, but the traceback shows up in the desktop app's
Server Details as "Recent Server Output" and looks like a failure. Treat
client disconnects as normal.

## Problem / Context

This was found in dogfood session 0.2 of `WI-LRH-CONSOLE-DESKTOP-DOGFOOD`. It
is defect D5 in `project/evidence/EV-LRH-CONSOLE-DESKTOP-L0-DOGFOOD.md`. The
owner thought it was "perhaps" caused by using Back. The request was
`/api/project`. Server Details' Recent Server Output then showed:

```text
Exception occurred during processing of request from ('127.0.0.1', 54062)
...
  File ".../src/lrh/serve.py", line 2803, in do_GET
    self._write_json(200, project_viewer_payload(config))
  File ".../src/lrh/serve.py", line 3066, in _write_json
    self.wfile.write(body)
...
BrokenPipeError: [Errno 32] Broken pipe
```

The traceback comes from the standard library, not from LRH code. Python's
`socketserver.BaseServer.handle_error` docs describe the default action as
printing "the traceback to standard error" and then carrying on with further
requests. `ThreadingHTTPServer` (`src/lrh/serve.py:2644`) does not override
it. The response helpers `_write_download` (`src/lrh/serve.py:3021`),
`_write_json` (`3066`), and `_write_text` (`3081`, which also serves HTML)
write without guarding against a closed peer.

### Duplication search

- In-repo: no existing work item or backlog entry covers Serve disconnect
  handling. `grep BrokenPipe src/lrh/serve.py` finds nothing.
- Recommendation: proceed.

## Scope

- Make client-disconnect errors during a response quiet in Serve's request
  handling, either in `handle_error` on the server class or around the
  response writes.
- Add a regression test.

## Required Changes

1. Treat `BrokenPipeError` and `ConnectionResetError` raised while handling a
   request as client disconnects: log nothing, or at most one short line, and
   keep serving. A narrow `handle_error` override on `ThreadingHTTPServer`
   that checks the active exception is one option. Guarding the write helpers
   is another. Choose one and document why.
2. Leave every other exception's reporting unchanged.
3. Add a real-socket regression test. It should open a connection to a route
   with a large enough body, close it before reading, then assert that
   stderr has no traceback and that `/health` still returns 200.

## Non-Goals

- No change to routes, payloads, or the desktop protocol.
- No logging framework changes.

## Acceptance Criteria

- A mid-response disconnect produces no traceback, and Serve keeps serving.
- Other handler exceptions are still reported.
- A regression test covers the disconnect.

## Validation

- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-DESKTOP-DOGFOOD`, whose evidence record
  documents the defect.

## Risk Notes

- Do not hide real server errors. The filter must match only disconnect
  errors raised during a request.
- A test that depends on exact socket buffer sizes can flake. Use a body much
  larger than typical socket buffers, or close the socket before the
  response starts.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/evidence/EV-LRH-CONSOLE-DESKTOP-L0-DOGFOOD.md`
