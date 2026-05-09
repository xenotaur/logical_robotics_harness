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

## Current sequencing update (2026-05-05)

Recently completed baseline work:

- control-plane model/parser/validation foundations (`WI-0001` through `WI-0004`)
- precedence resolver implementation and canonicalization closure validation (`WI-PRECEDENCE-RESOLVER`)
- package CLI adoption for `lrh request` and `lrh snapshot`
- reconciled near-term design basis that treats recursive planning-tree workstreams as accepted planning architecture

Immediate next ordering:

1. complete **Phase 01A — Planning Tree and Workstream Foundation** as the explicit planning
   prerequisite for the Workstream Control Plane MVP
2. then implement the Workstream Control Plane MVP through the scoped work items created by
   Phase 01A
3. represent workstreams as first-class, repo-native planning artifacts before automation
4. keep user-facing concepts simple and explicit: **Project -> Workstream -> Work Item**
5. keep parent/child structure metadata-driven rather than path-driven
6. keep metadata authoritative and treat directory buckets as navigation projections
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

Add operational behavior:
- work item execution scaffolding
- evidence recording
- synthesized status
- run artifacts

Exit condition:
- LRH can execute a bounded workflow and produce evidence-backed status.

## Phase 4 — MCP and Agent Integration

Add external orchestration capability:
- MCP integration
- tool registry
- agent runtime abstraction
- guardrail and approval controls

Exit condition:
- LRH can act as a practical harness around external tools and agent runtimes.
