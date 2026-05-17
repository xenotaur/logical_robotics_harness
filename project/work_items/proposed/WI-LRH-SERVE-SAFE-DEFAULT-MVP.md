---
resolution: null
blocked_reason: null
blocked: false
id: WI-LRH-SERVE-SAFE-DEFAULT-MVP
title: Define safe-default lrh serve viewer and prompt workbench MVP
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-EXECUTION-FRAMEWORK
related_design:
  - project/design/execution_framework_mvp.md
  - project/design/proposals/adopted/safe-default-agentic-extra-packaging/00_proposal.md
  - project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md
depends_on:
  - WI-LRH-CORE-STATE-APIS-MVP
  - WI-WORKSTREAM-PLANNING-TREE-RELATIONSHIPS-MVP
  - WI-PLANNING-TREE-VALIDATION-RULES-MVP
  - WI-WORKSTREAM-SNAPSHOT-MVP
  - WI-EXECUTION-READINESS-SCHEMA
  - WI-RUN-PACKET-DRY-RUN
  - WI-RUN-REPORT-MVP
blocked_by: []
expected_actions:
  - edit_file
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - safe-default serve scope is documented and implemented as a local viewer and prompt workbench
  - serve is introduced as a default-package CLI command backed by package code, with no optional web dependency until an implementation prompt selects one
  - serve consumes shared snapshot planning summaries and control-plane state APIs rather than inventing a workflow engine or tree interpreter
  - the read-only viewer renders project/workstream/work-item state, validation status, readiness metadata, and evidence/report affordances without filesystem browsing or secrets exposure
  - the prompt workbench previews and exports generated prompts, run packets, and run report drafts without dispatching agents or mutating branches
  - all writes remain deferred for this MVP except explicitly reviewed future control-artifact writes; no write may happen automatically on page load
  - autonomous dispatch, branch mutation, PR creation or mutation, CI-fix loops, review-fix loops, merge, release, and publish remain out of scope
required_evidence:
  - manual_review
  - validation_output
artifacts_expected:
  - documentation
  - tests
  - cli_command
---

## Summary

Define and later implement the safe-default `lrh serve` MVP as a local project-state viewer and
prompt workbench, not an autonomous runner. The package consumes existing LRH control-plane state,
planning summaries, execution-readiness metadata, run-packet rendering, and run-report rendering. It
must not introduce agent dispatch, branch mutation, PR creation or mutation, CI/review loops, merge,
release, publish, destructive actions, arbitrary filesystem browsing, or automatic state changes.

This work item is refined as one parent implementation package with four explicit slices rather than
new child work items. That keeps the next PR small while leaving clear boundaries for subsequent
implementation prompts.

## MVP Boundary Decisions

1. **Exact MVP scope:** a local-only browser surface for inspecting LRH project-control state and for
   previewing/copying/downloading generated prompt, run-packet, and run-report artifacts.
2. **Introduction shape:** add `lrh serve` as a normal safe-default CLI command backed by package code
   under `src/lrh/` when implementation begins. Do not create a separate package or optional extra for
   the skeleton unless concrete implementation pressure proves a dependency is needed.
3. **Local server dependency:** start with the Python standard library if practical. A small dependency
   may be proposed only in the local-server-skeleton implementation PR, with justification, tests, and
   no transitive expansion into agentic behavior.
4. **Read-only viewer includes:** project identity, validation status, current focus, workstreams,
   work items, planning-tree/active-leaf summaries, readiness metadata, evidence/status links, and
   report/checklist affordances sourced from existing LRH APIs and renderers.
5. **Read-only viewer excludes:** arbitrary filesystem browsing, secret display, external network
   calls, repository mutation, branch mutation, PR creation or mutation, workflow reruns, and any
   server-only planning-tree interpretation.
6. **Prompt workbench includes:** generated-prompt preview, editable in-browser text before export,
   copy/download fallback, run-packet preview using existing dry-run/request rendering, and run-report
   draft preview using the existing report renderer.
7. **Prompt workbench excludes:** agent backend dispatch, simulation claims, CI/review response loops,
   automatic execution-record updates, branch/PR mutation, merge/release/publish automation, and
   auto-saving generated artifacts.
8. **Writes:** defer writes for the MVP. A later PR may propose explicit-click writes only for narrow
   LRH control artifacts such as prompt packets, manual run records, evidence notes, report drafts, or
   execution records. No write may happen on page load, preview, validation, copy, or download.
9. **Default network posture:** bind to `127.0.0.1` by default. Do not bind to `0.0.0.0` unless a later
   prompt explicitly documents the risk, CLI spelling, and review evidence.
10. **Next prompt:** `PROMPT(WI-LRH-SERVE-SAFE-DEFAULT-MVP:IMPLEMENT_SERVE_LOCAL_SERVER_SKELETON)`.

## Future visual language direction

Future dashboard design work should use the proposed LRH Console visual language in
`project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md` as directional UX
guidance after the safe-default MVP stabilizes. That proposal now includes UX review criteria and a
first implemented `lrh serve` review checklist that reviewers can use to assess safe-default UI
tranches. The checklist is not a blocking acceptance criterion for this MVP and does not expand this
work item's read-only, safe-default implementation scope.

## Implementation Slices

### Slice 1 — Safe-default serve plan/control-plane refinement

Status: this planning slice should land before runtime code.

Required changes:

- Refine this work item with the package boundary, staged implementation plan, exclusions,
  validation commands, expected evidence, and next prompt.
- Refresh the execution-framework workstream and any stale roadmap/focus/status text so the next
  phase points at the serve package rather than completed prerequisite or execution-contract work.
- Add one prompt execution record for the planning prompt.

Acceptance criteria:

- The serve boundary answers the MVP scope, CLI/package shape, dependency posture, viewer scope,
  workbench scope, write policy, validation expectations, and next prompt.
- The workstream names `WI-LRH-SERVE-SAFE-DEFAULT-MVP` as the next package after completed
  prerequisites/contracts.
- No server, viewer, workbench, dependency, agent backend, mutation, or automation code is added.

Validation commands:

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `lrh snapshot project --stdout`

Expected evidence:

- Manual review of the changed planning/control-plane artifacts.
- Validation logs from the commands above or a documented setup/environment limitation.
- Execution record under `project/executions/WI-LRH-SERVE-SAFE-DEFAULT-MVP/`.

### Slice 2 — Local server skeleton

Next implementation prompt:
`PROMPT(WI-LRH-SERVE-SAFE-DEFAULT-MVP:IMPLEMENT_SERVE_LOCAL_SERVER_SKELETON)`.

Required changes:

- Add the `lrh serve` CLI entrypoint with explicit `--host` and `--port` options.
- Default host must be `127.0.0.1`; default port should be deterministic and documented.
- Serve only package-owned static/minimal HTML and JSON derived from the project root passed through
  LRH's existing project-root resolution.
- Use standard-library HTTP serving if practical; if a dependency is selected, document why the
  standard library is insufficient and keep it out of optional agentic packaging.
- Add unit tests for CLI option parsing, default host behavior, project-root resolution, and no
  automatic writes.

Acceptance criteria:

- `lrh serve --help` documents safe-default local-only behavior and explicit exclusions.
- The skeleton can start locally and render a minimal health/index page without loading secrets or
  browsing arbitrary paths.
- No file is created or modified by starting the server.
- Binding to `0.0.0.0` is unavailable or requires an explicit non-default flag with warning text.
- No web framework dependency is added unless the PR includes dependency justification and tests.

Validation commands:

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `lrh snapshot project --stdout`
- focused CLI/server tests added in the PR

Expected evidence:

- Test output for the CLI/server skeleton.
- Manual smoke evidence showing the server binds to `127.0.0.1` and serves the minimal index.

### Slice 3 — Read-only project/workstream/work-item viewer

Required changes:

- Render project identity, validation summary, current focus, active workstreams, active work items,
  planning-tree/active-leaf summaries, readiness status, and evidence/status links from shared LRH
  APIs.
- Reuse the same planning summary consumed by `lrh snapshot`; do not duplicate relationship
  inference inside the server layer.
- Add tests for rendered model construction and redaction/omission of secrets or unsupported files.
- Document that the viewer is a local assist UI, not a security sandbox or autonomous runner.

Acceptance criteria:

- Viewer output is read-only and deterministic for a fixture project.
- Viewer state agrees with `lrh snapshot` for planning-tree and active-leaf summaries.
- No arbitrary filesystem browsing route exists.
- No automatic writes, external network calls, agent dispatch, branch mutation, or PR mutation exist.

Validation commands:

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `lrh snapshot project --stdout`
- focused viewer model/rendering tests added in the PR

Expected evidence:

- Unit test output for viewer projection.
- Manual review or screenshot only if a perceptible web UI change is introduced.

### Slice 4 — Prompt/run-packet/report workbench MVP

Required changes:

- Add a workbench view that previews generated prompts, run packets, and run-report drafts using
  existing LRH request/rendering paths.
- Provide copy/download flows that do not imply execution, simulation, dispatch, or persistence.
- Keep editable text in browser memory only for the MVP unless a later explicit-write prompt narrows
  and approves artifact persistence.
- Add tests proving workbench generation calls existing renderers and does not dispatch agents,
  mutate branches, create PRs, or write artifacts by default.

Acceptance criteria:

- A user can select a work item and preview/copy/download the generated prompt/run packet/report
  text.
- The UI labels artifacts as preview/export outputs, not executed runs.
- No execution record, evidence note, run state, branch, PR, or report file is written by default.
- Any future explicit-click write is separately justified and limited to LRH control artifacts.

Validation commands:

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `lrh snapshot project --stdout`
- focused workbench renderer/no-write tests added in the PR

Expected evidence:

- Unit test output for workbench generation and no-write behavior.
- Manual smoke evidence for preview/copy/download fallback.

## Cross-Slice Non-Goals

- No autonomous runtime execution.
- No agent backend adapters or dispatch.
- No branch mutation, force pushes, repository mutation, or destructive operations.
- No PR creation, PR mutation, workflow reruns, CI-fix loops, review-response loops, merge, release,
  or publish automation.
- No arbitrary filesystem browsing or secret rendering.
- No automatic state change on page load, validation, preview, copy, or download.
- No server-only planning-tree interpreter; consume shared state/snapshot APIs.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-EXECUTION-FRAMEWORK.md`
- Canonical execution framework design: `project/design/execution_framework_mvp.md`
- Adopted safe-default agentic packaging proposal:
  `project/design/proposals/adopted/safe-default-agentic-extra-packaging/00_proposal.md`

## Risk Notes

- A local server could be mistaken for an autonomous runner unless the default capability boundary is
  explicit in CLI help, docs, UI labels, and tests.
- A local server could be mistaken for a sandbox unless documentation explains that it is a local
  assist UI with conservative defaults, not an isolation boundary.
- Write conveniences could accidentally broaden into mutation-capable workflow automation; keep them
  deferred until a later explicit-write prompt justifies a narrow artifact boundary.
- Adding a web framework too early could obscure the safe-default skeleton and widen the dependency
  surface before the minimal viewer proves what it needs.

## Dependencies / Order

The prerequisite control-plane alignment and first execution-contract package are complete. The serve
package can now proceed in this order:

1. safe-default serve plan/control-plane refinement;
2. local server skeleton;
3. read-only project/workstream/work-item viewer;
4. prompt/run-packet/report workbench MVP.

Later packages may add durable run state, read-only observation adapters, and optional agentic
capability only after the safe-default viewer/workbench boundary remains stable and reviewed.
