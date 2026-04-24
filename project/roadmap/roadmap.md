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

## Current sequencing update (2026-04-22)

Recently completed baseline work:

- control-plane model/parser/validation foundations (`WI-0001` through `WI-0004`)
- precedence resolver implementation and canonicalization closure validation (`WI-PRECEDENCE-RESOLVER`)
- package CLI adoption for `lrh request` and `lrh snapshot`

Immediate next ordering:

1. preserve package-owned templates + package-resource loading behavior
2. maintain packaging/installability hardening with installed-package smoke checks
3. keep canonical survey command surface on `lrh survey` backed by `src/lrh/assist/sourcetree_surveyor.py`
4. pursue follow-on `sourcetree_surveyor` capability expansion only when a concrete downstream consumer defines required structured fields (schema expansion intentionally deferred)

Prompt-workflow integration note:

- meaningful prompt-driven documentation or implementation work should use `PROMPTS.md` conventions and add an execution record under `project/executions/`
- reruns should preserve prior execution history and link via `rerun_of` rather than rewriting prior records

Meta-control planning guardrail:

- before widening Meta CLI surface beyond the current MVP command set, align and land the shared workspace-resolution contract (explicit precedence, XDG-style global defaults, explicit local mode, and visible resolution behavior)

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
