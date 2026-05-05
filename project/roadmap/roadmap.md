---
id: ROADMAP-CORE
title: Logical Robotics Harness Roadmap
status: active
owner: human_agent
time_horizon: medium
children:
  - ROADMAP-PHASE-01
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

1. plan and implement the **Workstream Control Plane MVP** as the next active phase
2. represent workstreams as first-class, repo-native planning artifacts before automation
3. keep user-facing concepts simple and explicit: **Project -> Workstream -> Work Item**
4. keep parent/child structure metadata-driven rather than path-driven
5. keep metadata authoritative and treat directory buckets as navigation projections
6. sequence work through small reviewable work items before any execution-framework implementation

Prompt-workflow integration note:

- meaningful prompt-driven documentation or implementation work should use `PROMPTS.md` conventions and add an execution record under `project/executions/`
- reruns should preserve prior execution history and link via `rerun_of` rather than rewriting prior records

## Near-term roadmap addition: Workstream Control Plane MVP

MVP goal:

> LRH can represent, validate, and summarize workstreams as first-class project-control artifacts before implementing automation.

Recommended MVP deliverables (sequenced across focused work items):

- `project/workstreams/` directory structure and README
- minimal workstream frontmatter/schema documentation
- workstream loader/model support
- workstream validation for status, stage, IDs, and bucket/status consistency
- planning-tree index or parent/child reference validation (as scoped)
- snapshot summary of workstreams
- dry-run-first organize/tidy support after validation behavior is stable

Explicitly deferred to the long-term execution-framework architecture:

- `lrh run`
- agent runtime execution
- workstream orchestrator
- automated stage advancement
- MCP bridges
- telemetry systems
- execution backends/adapters (Claude, Codex, native, Spec Kit, etc.)

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
