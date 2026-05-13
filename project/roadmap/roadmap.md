---
id: ROADMAP-CORE
title: Logical Robotics Harness Roadmap
status: active
owner: human_agent
time_horizon: medium
children:
  - ROADMAP-PHASE-01
  - ROADMAP-PHASE-01A
  - ROADMAP-PHASE-02
  - ROADMAP-PHASE-03
  - ROADMAP-PHASE-04
---

# Roadmap

The harness should be built in stages, with the earliest stages proving the project model and local
workflow before deeper agent integration.

## Current sequencing update (2026-05-13)

Recently completed baseline work:

- control-plane model/parser/validation foundations (`WI-0001` through `WI-0004`)
- precedence resolver implementation and canonicalization closure validation (`WI-PRECEDENCE-RESOLVER`)
- package CLI adoption for `lrh request` and `lrh snapshot`
- reconciled near-term design basis that treats recursive planning-tree workstreams as accepted planning architecture

Immediate next ordering:

1. treat the Workstream Control Plane MVP as the landed prerequisite for execution-framework planning
2. plan **Phase 3 — Execution, Evidence, and Status** as a staged bounded execution-framework phase
3. begin the first execution-contract package with execution readiness, dry-run run packets, and run reports for selected work items
4. keep user-facing concepts simple and explicit: **Project -> Workstream -> Work Item -> Run Packet -> Run Report**
5. preserve human/policy gates for merge, release, publish, and closeout
6. keep branch mutation, autonomous stabilization, and backend adapters deferred until contracts are stable
7. sequence work through small reviewable work items before any execution-framework implementation

Prompt-workflow integration note:

- meaningful prompt-driven documentation or implementation work should use `PROMPTS.md` conventions and add an execution record under `project/executions/`
- reruns should preserve prior execution history and link via `rerun_of` rather than rewriting prior records

## Near-term roadmap addition: Planning Tree and Workstream Foundation (Safe-Default Compatible)

MVP goal:

> LRH can represent planning-tree semantics and workstreams as core non-agentic project-control artifacts before implementing automation.

Recommended MVP deliverables (sequenced across focused work items):

- planning-node schema conventions for `parent_id` and `children`
- execution-ready work item concept for human-executable leaves
- planning-tree validation rule design for cycles, references, and consistency
- `project/workstreams/` directory structure and README
- minimal workstream frontmatter/schema documentation (`id`, `status`, `stage`, `parent_id`)
- workstream-to-work-item relationship conventions
- snapshot visibility design for workstreams
- human-assisted run-packet or execution-prompt generation design with no autonomous execution implied
- follow-on implementation slices for loader/model, validation, snapshot, and dry-run-first organize/tidy support

Explicitly deferred to the long-term execution-framework architecture:

- `lrh agentic run` / autonomous run commands (deferred / future / requires `lrh[agentic]`)
- agent adapters (deferred / future / requires `lrh[agentic]`)
- PR stabilization loops (deferred / future / requires `lrh[agentic]`)
- sandbox envelope work (deferred / future / requires `lrh[agentic]`)
- agent runtime execution
- workstream orchestrator
- automated stage advancement
- MCP bridges
- telemetry systems
- execution backends/adapters (Claude, Codex, native, Spec Kit, etc.)

Command naming note: planning artifacts should use `lrh agentic run` or `lrh-agentic run` when
referring to future autonomous execution. Older accepted design notes that mention `lrh run` should
be read as deferred execution-framework shorthand, not as a safe-default command commitment. If an
integrated `lrh run` alias is ever introduced for autonomous behavior, it must require the optional
agentic capability and be unavailable in the default non-agentic install.


## Near-term roadmap addition: Bounded Agent Execution Framework

Canonical living design: `project/design/execution_framework_mvp.md`. The workstream is staged as prerequisite control-plane alignment, first execution contracts, read-only/local-assist workbench, ecosystem observation, and only later bounded runtime execution.

MVP goal:

> LRH can prepare and eventually run bounded, auditable execution workflows for selected executable
> leaves, using run packets, branch-contained PR stabilization, validation evidence, and final run
> reports while preserving human/policy gates.

Recommended staged deliverables:

The first implementation package is not this entire list. The selected first package is the
execution-contract sequence: `WI-EXECUTION-READINESS-SCHEMA`, `WI-RUN-PACKET-DRY-RUN`, and
`WI-RUN-REPORT-MVP`. Items before that are prerequisites to verify or complete separately; items
after that are deferred follow-on packages.

Prerequisite control-plane alignment:

1. **Shared core state APIs** — expose one reusable interpretation of project-control state for CLI,
   request, serve, snapshot, and future dry-run surfaces.
2. **Planning relationship/index validation** — validate workstream/work-item relationships before UI
   or runtime surfaces infer planning-tree state.
3. **Snapshot-visible planning summaries** — make planning-tree state visible through snapshots before
   or alongside later `lrh serve` work.

First execution-contract package:

1. **Execution readiness schema** — define the opt-in work-item fields required before a selected leaf
   can be used for future run-packet generation or execution workflows.
2. **Run packet dry-run** — generate a human-reviewable packet without invoking an agent or mutating
   branches.
3. **Run report MVP** — define and generate final Markdown reports with status, validation evidence,
   human verification tasks, and recommended next actions.

Deferred follow-on packages:

1. **Safe-default `lrh serve` viewer and prompt workbench** — render shared state and first-package
   contracts without becoming an autonomous runner or separate tree interpreter.
2. **Agent branch containment design support** — document agent-owned branch namespaces, protected
   merge gates, and branch policy assumptions before mutation-capable behavior.
3. **GitHub PR/CI observation adapter** — read PR, review, and CI state without repository mutation.
4. **Bounded stabilization loop design** — plan iteration limits, stop conditions, and escalation
   rules before automation can respond to review or CI.
5. **Backend adapter abstraction** — define backend-neutral contracts only after packet/report and
   policy boundaries are stable.
6. **Manual/assisted/bounded-auto mode progression** — preserve manual-mode parity before assisted
   or bounded-auto execution.

First execution-contract package after this planning PR:

1. `WI-EXECUTION-READINESS-SCHEMA`
2. `WI-RUN-PACKET-DRY-RUN`
3. `WI-RUN-REPORT-MVP`

Prerequisites to verify before that package starts: shared core state APIs, planning
relationship/index validation, and snapshot-visible planning summaries. Safe-default `lrh serve` is
a deferred read-only/local-assist package, not part of the first execution-contract package.

Explicitly deferred until later phases or optional capability work:

- automatic merge to main
- release or publish automation
- secrets management beyond documented policy assumptions
- privileged workflow execution
- MCP bridges
- telemetry systems
- full autonomous execution
- backend-specific implementations until contracts are stable
- autonomous branch mutation before readiness, packet, and report contracts exist

## Phase 1 — Control Plane

Define and implement the project control model:
- principles
- goal
- roadmap
- focus
- work items
- evidence
- status

Exit condition:
- LRH can parse and validate a project directory and expose its contents coherently.

## Phase 2 — Runtime and Workspace

Add project-repo interaction:
- workspace discovery
- workspace adapter interface
- CLI surface
- end-to-end handling of a target repository

Exit condition:
- LRH can run against a sample project repository and identify current focus and work queue.

## Phase 3 — Execution, Evidence, and Status

Phase 3 is now staged by the bounded execution-framework plan above. The canonical phase detail lives
in `project/roadmap/phase_03_execution_evidence_status.md`, starting with execution readiness,
dry-run run packets, and run reports before mutation-capable automation, PR stabilization loops, or
agent backends.

Exit condition:
- LRH can prepare bounded, evidence-backed execution artifacts and later execute bounded workflows
  only after readiness, packet, report, and human/policy-gate contracts are stable.

## Phase 4 — MCP and Agent Integration

Add external orchestration capability:
- MCP integration
- tool registry
- agent runtime abstraction
- guardrail and approval controls

Exit condition:
- LRH can act as a practical harness around external tools and agent runtimes.
