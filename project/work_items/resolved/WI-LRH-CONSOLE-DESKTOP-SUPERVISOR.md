---
id: "WI-LRH-CONSOLE-DESKTOP-SUPERVISOR"
title: "Implement the LRH Console Rust supervisor for the owned Serve backend"
type: "deliverable"
status: "resolved"
blocked: false
blocked_reason: null
resolution: 'Implemented and merged in PR #758 (commit 6977ce46): Rust supervisor for desktop-server-protocol v1 (apps/desktop/src-tauri/src/supervisor.rs) with 17 real-child integration tests, including parent loss and unrelated-server isolation on macOS and Linux CI; also removed the reverse-DNS lookup in serve.ThreadingHTTPServer.server_bind that stalled startup on macOS runners.'
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
- "docs/reference/desktop-server-protocol.md"
depends_on:
- "WI-LRH-CONSOLE-DESKTOP-PROTOCOL"
- "WI-LRH-CONSOLE-DESKTOP-L0"
blocked_by: []
expected_actions:
- "create_file"
- "edit_file"
- "run_tests"
- "write_docs"
- "create_pr"
forbidden_actions:
- "force_push"
- "delete_branch"
- "merge_pr"
- "publish_package"
- "deploy_remote_service"
- "implement_project_mutation"
- "run_lrh_agentic"
- "implement_lrh_console_desktop_shell"
acceptance:
- "A Rust supervisor module in apps/desktop/src-tauri implements desktop-server-protocol v1: it serializes stopped/starting/running/stopping/failed transitions, makes Start idempotent, and makes Restart wait for the previous owned child to exit."
- "Readiness and stop are bounded by the protocol's timeout defaults. Stale callbacks, wrong protocol versions, and wrong workspaces are rejected with typed errors."
- "The supervisor only ever controls the child handle it spawned. It never adopts, signals, or kills a process found by name or port, and it adds no HTTP shutdown route."
- "supervisor_test.rs drives a real lrh serve --desktop-protocol child through start, idempotent start, restart, stop, readiness timeout, crash, and incompatible-version cases, and proves that a separately started lrh serve stays untouched by Start, Stop, Restart, and failure. It runs in scripts/test --desktop and passes in desktop CI on Linux and macOS."
- "Parent loss is proven on macOS: when the supervising process dies, the owned child exits within the protocol bound and no orphan remains."
required_evidence:
- "manual_review"
- "lrh_validate"
- "test_output"
- "validation_output"
artifacts_expected:
- "apps/desktop/src-tauri/src/supervisor.rs (or an equivalent supervisor module)"
- "apps/desktop/src-tauri/tests/supervisor_test.rs"
- "docs/how-to/project-setup/desktop-toolchain.md (tier-1 supervisor test notes, if the commands change)"
---

# LRH Console desktop supervisor

## Summary

Implement the native Rust supervisor that the LRH Console app uses to own one
`lrh serve --desktop-protocol` backend. It is a headless library module with
integration tests. The menus and windows that call it belong to
`WI-LRH-CONSOLE-DESKTOP-SHELL`, and the settings, recovery pages, and browser
handoff to `WI-LRH-CONSOLE-DESKTOP-SETTINGS` (split from SHELL on 2026-09-30).

## Problem / Context

This item was split out of `WI-LRH-CONSOLE-DESKTOP-L0` (its Required Changes
item 2), so that each work item maps to one PR.

- `WI-LRH-CONSOLE-DESKTOP-PROTOCOL` landed the versioned contract, documented
  in `docs/reference/desktop-server-protocol.md`, together with a Python
  reference supervisor (`src/lrh/desktop_supervisor.py`).
- `WI-LRH-CONSOLE-DESKTOP-L0` landed the toolchain, the scripts, and a minimal
  Tauri app in PR #750.

Process lifetime is where the subtle bugs live, so the supervisor lands and
gets reviewed on its own, before any UI depends on it.

### Duplication search

- In-repo: `src/lrh/desktop_supervisor.py` is the Python reference
  implementation of the same rules. Port its state machine and cases rather
  than inventing new semantics. There is no Rust supervisor in
  `apps/desktop/` at `9eeea442`.
- External libraries: use the Rust standard library process APIs and the
  pinned Tauri runtime. Add a process-management crate only if the protocol's
  parent-loss rule needs it, and pin it exactly.
- Recommendation: proceed.

### Demand search

- Work items: this is the direct successor to `WI-LRH-CONSOLE-DESKTOP-L0`, and
  `WI-LRH-CONSOLE-DESKTOP-SHELL` depends on it.
- Recommendation: proceed. No other request is satisfied or superseded.

## Scope

- A supervisor module, its state machine, and typed errors.
- Integration tests against a real backend child.
- No menus, windows, settings persistence, or recovery pages.

## Required Changes

1. Add a supervisor module under `apps/desktop/src-tauri/src/`. It implements
   desktop-server-protocol v1: spawn, ready handshake, endpoint and workspace
   identity, shutdown, and parent loss.
2. Serialize the stopped, starting, running, stopping, and failed transitions.
   - Start is idempotent: a second Start while starting or running creates no
     second child.
   - Restart waits for the previous owned child to exit before it spawns a new
     one.
   - Reject stale callbacks from an earlier child generation, and reject a
     wrong protocol version or wrong workspace, with typed errors.
3. Bound readiness and stop with the protocol's timeout defaults, and escalate
   only against the owned child handle. Never kill by name or port, never
   adopt an unrelated server, and add no HTTP shutdown endpoint.
4. Capture bounded diagnostic output from the child (stdout and stderr tails)
   for later display, without logging environment variables.
5. Add `apps/desktop/src-tauri/tests/supervisor_test.rs`. It drives a real
   `lrh serve --desktop-protocol` child through these cases:
   - start, idempotent start, restart, and stop;
   - a readiness timeout;
   - a child crash;
   - an incompatible version;
   - parent loss;
   - a separately started `lrh serve` that stays untouched by Start, Stop,
     Restart, and failure.

   The tests find the `lrh` executable explicitly, through an environment
   variable or the repository's `PYTHONPATH=src` invocation, not through an
   implicit shell PATH. On a machine without the desktop toolchain the tests
   are skipped, because they only run under `scripts/test --desktop`.
6. Update `docs/how-to/project-setup/desktop-toolchain.md` if the tier-1
   commands or prerequisites change.

## Non-Goals

- No native menus, windows, settings storage, recovery pages, or
  browser handoff. Menus and windows belong to `WI-LRH-CONSOLE-DESKTOP-SHELL`;
  settings storage, recovery pages, and browser handoff belong to
  `WI-LRH-CONSOLE-DESKTOP-SETTINGS` (split from SHELL on 2026-09-30).
- No change to the Python protocol or to `lrh serve` behavior. If a protocol
  gap is found, record it and propose a protocol revision rather than working
  around it.
  - Scope revision (2026-09-30, approved by the owner during PR #758): a
    backend defect that the supervisor tests expose may be fixed here when
    the fix leaves the protocol and observable Serve behavior unchanged. The
    first such fix removes the reverse-DNS lookup (`socket.getfqdn`) that
    `http.server.HTTPServer.server_bind` performs. That lookup stalled startup
    about 25 s on GitHub's macOS runners, past the 20 s startup budget.
- No dogfood evidence. That belongs to `WI-LRH-CONSOLE-DESKTOP-DOGFOOD`.

## Acceptance Criteria

- A Rust supervisor module implements desktop-server-protocol v1 with
  serialized transitions, idempotent Start, and a Restart that waits for the
  previous child to exit.
- Readiness and stop are bounded. Stale callbacks, wrong versions, and wrong
  workspaces are rejected with typed errors.
- Only the owned child handle is ever controlled. There is no kill by name or
  port and no HTTP shutdown route.
- `supervisor_test.rs` covers the listed lifecycle and failure cases against a
  real child, including an unrelated server that stays untouched, and passes
  in desktop CI on Linux and macOS.
- Parent loss is proven on macOS, with no orphan left behind.

## Validation

- `lrh validate`
- `scripts/format --check --diff --desktop`
- `scripts/lint --desktop`
- `scripts/test --desktop`
- `scripts/test` (default run, still Rust-free, prints the desktop SKIPPED line)
- `scripts/check-workflows`

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-DESKTOP-PROTOCOL` (resolved) and
  `WI-LRH-CONSOLE-DESKTOP-L0` (the toolchain and minimal app).
- `WI-LRH-CONSOLE-DESKTOP-SHELL` depends on this item.

## Risk Notes

- On macOS, process lifetime differs from app lifetime. Test parent crash
  explicitly; a happy-path smoke test is not enough.
- A supervisor that signals anything other than its own child handle could
  stop an unrelated server. The tests must prove that a separately started
  server is untouched.
- The tests use a real child, so they must bound every wait and clean up on
  failure, so that one failing test cannot hang CI.

## Related Workstream and Designs

- `project/workstreams/proposed/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md`
- `docs/reference/desktop-server-protocol.md`

## Open Questions

Confirm whether the protocol's parent-loss mechanism (stdin close) needs any
extra macOS handling in Rust, and whether the timeout defaults need to be
configurable at this layer or only in `WI-LRH-CONSOLE-DESKTOP-SETTINGS`'s
settings.
