---
resolution: 'Implemented and merged in PR #727 (commit d9f0e49e): versioned lrh serve --desktop-protocol, reference supervisor, protocol reference, unit/smoke tests, and EV-LRH-CONSOLE-DESKTOP-PROTOCOL.'
blocked_reason: null
blocked: false
type: "deliverable"
status: "resolved"
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
required_evidence:
- "manual_review"
- "lrh_validate"
- "test_output"
- "validation_output"
id: "WI-LRH-CONSOLE-DESKTOP-PROTOCOL"
title: "Define and implement the LRH desktop server protocol"
depends_on: []
acceptance:
- "Owned child returns a supported handshake with actual loopback endpoint, versions, and matching launch/workspace\
  \ identity."
- "Invalid input, incompatible protocol, workspace errors, and startup failures produce bounded actionable outcomes."
- "Graceful shutdown and parent-channel loss terminate the owned backend within documented deadlines without affecting\
  \ unrelated servers."
- "The contract defines restart ordering, stale-event handling, and parent/child responsibilities for the desktop\
  \ shell."
- "Normal foreground Serve and existing read-only/security behavior remain compatible; runtime readiness grants\
  \ no execution authority."
- "Canonical validation and protocol failure-path tests pass with actual evidence and documented platform limits."
artifacts_expected:
- "src/lrh/desktop_protocol.py (proposed module boundary)"
- "src/lrh/desktop_supervisor.py (minimal reference supervisor and runnable example)"
- "src/lrh/serve.py and existing Serve CLI integration"
- "docs/reference/desktop-server-protocol.md"
- "tests/cli_tests/desktop_protocol_test.py"
- "tests/cli_tests/desktop_supervisor_test.py"
- "tests/smoke/desktop_protocol_smoke.py"
- "project/evidence/EV-LRH-CONSOLE-DESKTOP-PROTOCOL.md"
---

# Desktop startup and lifecycle protocol for LRH Serve

## Summary

Give a desktop supervisor a documented machine interface for starting and stopping
its own LRH Serve process, confirming the actual loopback endpoint and workspace,
and cleaning up on parent loss. Preserve ordinary foreground CLI behavior.

## Problem / Context

The Dock app cannot reliably discover ownership or readiness by parsing human
startup text or finding an occupied port. `src/lrh/serve.py:108-130` currently
reports service status without a versioned launch identity, while
`src/lrh/serve.py:3141-3169` implements a foreground server loop. The shell needs
an explicit contract before its controls can be trustworthy. Source references
are at `8603b6514329ea242294da420aa448d2fc959fd1`.

### Duplication search

- In-repo: extend `src/lrh/serve.py` and its CLI integration. Host validation and
  read-only routing already exist; a desktop startup/parent-liveness contract was
  not found in tracked source or planning artifacts.
- Sibling repos: LCATS is a consumer candidate; not inspected for this capture.
- External libraries: use standard Python process/IPC facilities and Tauri's
  native process integration in the following item; no new server framework needed.
- Recommendation: proceed as a bounded extension, not a replacement server.

### Demand search

- Work items: the companion desktop L0 item consumes this contract; no separate
  existing protocol leaf was found in the inspected baseline.
- Proposals: Serve operational triage and console visual language are related
  consumers; this item does not complete either proposal.
- Backlog: blocked-field propagation is relevant to L1, not protocol scope.
- Recommendation: link the companion proposal/workstream; close no other demand.

## Scope

- Versioned startup, readiness, diagnostics, shutdown, and parent-liveness contract
  for an explicitly configured executable and one explicit workspace.
- Loopback-only binding with OS-assigned port discovery and clear failure results.
- CLI compatibility plus hermetic unit tests and bounded process integration tests.

## Required Changes

1. Add the protocol domain/serialization boundary, proposed as
   `src/lrh/desktop_protocol.py`; wire an explicit desktop mode through the existing
   Serve CLI and `src/lrh/serve.py`. Inspect actual CLI definitions before choosing
   flags. Document exact command/arguments, framing, message sizes, and versioning
   in a new `docs/reference/desktop-server-protocol.md`.
2. Define startup request and ready/failed response fields: protocol version,
   backend version, launch ID, effective workspace context, and actual bound
   endpoint. Bind first, then signal ready on a dedicated machine channel; keep
   logs separate. Use OS port allocation rather than a fixed-port race. Reject
   invalid/nonlocal targets and mismatched workspace selection explicitly.
3. Define a private parent-control/liveness channel, graceful stop, startup and
   shutdown deadlines, failure/exit codes, and parent-disconnect cleanup. The
   backend must not survive a lost supervising parent indefinitely. Use actual
   child/channel ownership; launch IDs correlate messages, not authenticate them.
4. State how the future shell serializes start/restart, ignores stale events, and
   waits for child exit. Define timeout/escalation responsibilities so the shell
   can stop only its owned child. No unauthenticated HTTP shutdown endpoint and no
   process discovery/termination by name or port.
5. Preserve current CLI output/foreground behavior outside desktop mode, normal
   project diagnostics, read-only routes, and HTTP security headers. Runtime
   ready does not mean the project validates or tasks may execute.
6. Add `tests/cli_tests/desktop_protocol_test.py` using the repository's
   `unittest.TestCase` conventions and `tests/smoke/desktop_protocol_smoke.py` for
   bounded real-process integration coverage of malformed/incompatible input, invalid paths,
   readiness/failure ordering, port discovery, disconnect/EOF, and graceful stop.
   Keep real-process checks under the existing smoke conventions. Record actual
   commands, versions, results, and platform limits in
   `project/evidence/EV-LRH-CONSOLE-DESKTOP-PROTOCOL.md` using the evidence schema.
   Supply exact commands in the protocol document, plus a minimal supervisor
   example or test driver demonstrating the contract without a Tauri build.
   Implementation placed that reference supervisor in
   `src/lrh/desktop_supervisor.py` (runnable as `python -m lrh.desktop_supervisor`)
   with hermetic checks in `tests/cli_tests/desktop_supervisor_test.py`; the smoke
   suite drives real processes through it.

The listed test and evidence paths are planned outputs of this implementation
item, not files delivered by the planning PR. If implementation refines their
locations, update `artifacts_expected` and this section together before closeout.

## Non-Goals

- Do not build the Tauri UI, graph renderer, or runtime bundle in this item.
- Do not add remote access, external-server adoption, project writes, agent
  execution, login services, or automatic executable/environment discovery.
- Do not replace existing human-facing Serve output with machine output by default.

## Acceptance Criteria

- An explicitly launched child returns a parseable supported handshake containing
  the bound loopback endpoint, matching launch/workspace identity, and versions.
- Wrong executable/protocol inputs, missing/invalid workspace, bind/start failure,
  and startup timeout produce bounded actionable failure without claiming ready.
- Graceful shutdown and loss of the private parent-liveness channel terminate the
  owned backend within the documented deadline; no unrelated service is signaled.
- The contract documents restart serialization, stale-event rejection, and
  parent/child responsibilities sufficiently for the L0 shell to consume it.
- Normal `lrh serve` remains compatible; readiness does not grant execution
  authority and existing read-only/security behavior remains covered.
- Canonical Python validation passes and evidence includes the actual protocol
  example, failure tests, and any platform limits rather than only a happy path.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- Run the exact bounded process/smoke commands added to `docs/reference/desktop-server-protocol.md`; capture startup, stop, parent-loss, mismatch, and unaffected-unrelated-server evidence.

## Dependencies / Order

This is the first new leaf; `depends_on` is empty because existing Serve support
is already in the inspected baseline. Its implementation and reviewed contract
must land before `WI-LRH-CONSOLE-DESKTOP-L0` starts consuming it. Planning readiness
is not activation or authorization to implement.

## Risk Notes

- A ready HTTP response from a different process is not proof of ownership.
- Buffering/log contamination can corrupt a startup stream; framing and flushing
  require tests. Connection/pipe inheritance can prevent expected EOF cleanup.
- Workspace fallback can mask a wrong project; validate effective identity.
- Signal/pipe behavior differs across platforms; document proven platforms and
  have the later Mac shell validate its actual process boundary.

## Related Workstream and Designs

- `project/workstreams/proposed/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md`
- `project/design/execution_framework_mvp.md`

## Open Questions

Resolve framing/transport, version negotiation, shutdown deadlines, and the
smallest explicit CLI entry point in this implementation. Record the decision in
the protocol reference; a reviewed contract and working tests are the deliverable,
not a prerequisite silently assumed to exist today.
