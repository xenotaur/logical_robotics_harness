---
id: WS-LRH-ASSISTANTS
kind: planning_node
title: LRH Assistants
status: active
stage: executing
origin: design_review
summary: Deliver the LRH assistant artifact class — a persistent, backend-neutral organizational role — in the staged, docs-first sequence defined by PROP-LRH-ASSISTANTS, keeping runtime behind durable run state and the sandbox envelope.
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-04
related_design:
  - project/design/proposals/adopted/lrh-assistants/00_proposal.md
  - project/design/proposals/proposed/constitutional-sandbox-envelope/00_proposal.md
work_items:
  - WI-LRH-ASSISTANTS-STAGE-1
exit_criteria:
  - PROP-LRH-ASSISTANTS is adopted with its open questions resolved
  - the assistant artifact-class convention is documented (README, token vocabulary, one worked package)
  - typed models (Assistant, AssistantProfile, AssistantBinding) land with validation and tests, dataclasses in src/lrh/control and behavior in a new src/lrh/assistants package
  - read-only inspection and context rendering (lrh assistant list / inspect / context) ship behind safe defaults with no dispatch or mutation
  - communication semantics, reviewed memory governance, and evaluation fixtures are delivered
  - a dogfood pilot binds one real assistant to one root workstream and is evaluated end to end
  - durable run integration and scheduled supervision are delivered only after durable run state and the sandbox envelope exist
---

# WS-LRH-ASSISTANTS — LRH Assistants

## Purpose

Deliver the LRH **assistant** artifact class defined by
[`PROP-LRH-ASSISTANTS`](../../design/proposals/adopted/lrh-assistants/00_proposal.md):
a persistent, backend-neutral organizational role that an arbitrary capable
agent (Claude, Codex, Jules, or a human) can instantiate to manage a bounded
workstream under explicit policy. The assistant models **how an assigned
manager operates** — an axis orthogonal to the planning tree (what the project
is doing), the run tree (execution), and contributor records (who acted).

This workstream owns the staged delivery. It keeps the aggressive parts —
autonomous launching, monitoring, scheduling, and run mutation — sequenced
behind LRH's durable run state and the constitutional sandbox envelope, exactly
as the proposal requires.

## Rationale

LRH's control plane has no model of a reusable mandate with a permission
ceiling, review policy, communication contract, and reviewed memory. The
adopted design fills that gap with a single new artifact class and defers
missions, engagements, teams, and scheduling until a demonstrated need. A
docs-first first increment lets the convention be reviewed and dogfooded before
any Python or runtime authority is introduced.

## Phases

The proposal defines Stages 0–10. This workstream tracks them as leaves:

- **Stage 0 — Design adoption.** `PROP-LRH-ASSISTANTS` adopted; open questions
  resolved. (Delivered with Stage 1.)
- **Stage 1 — Documentation-only package convention.** `project/assistants/`
  README, token vocabulary, and one fully worked package. No Python.
  → `WI-LRH-ASSISTANTS-STAGE-1`.
- **Stage 2 — Typed models and loaders.** `Assistant`, `AssistantProfile`,
  `AssistantBinding`, assistant fields on `Workstream`, and the optional
  `assistant_role:` execution-record field. Dataclasses in `src/lrh/control`;
  behavior and CLI in a new `src/lrh/assistants` package. (Future WI.)
- **Stage 3 — Validation.** Package, cross-file, policy-token (against the
  Stage 1 vocabulary), binding, memory-state, and path-safety checks.
- **Stage 4 — Core-state projection.** `AssistantState`,
  `AssistantBindingState`, `assistants_by_id`.
- **Stage 5 — Inspection and context rendering.** Read-only
  `lrh assistant list | inspect | context`.
- **Stage 6 — Communication semantics and rendering.**
- **Stage 7 — Memory and evaluations.**
- **Stage 8 — Dogfood pilot.** Bind `serve-interface-steward` to one root
  workstream; evaluate manually.
- **Stage 9 — Durable run integration.** Sequenced behind durable run state.
- **Stage 10 — Scheduled / event-driven supervision.** Only after durable
  state and adapters exist.

## Work-item leaves

- `WI-LRH-ASSISTANTS-STAGE-1` — Stage 1 docs-only package convention (this
  PR). Later stages are filed as their own work items as they become ready;
  Stages 9–10 remain gated behind durable run state.

## Non-goals

- No runtime behavior, launching, monitoring, scheduling, or run mutation in
  the near-term stages.
- No `project/engagements/`, assistant teams, or multi-root delegation until
  the promotion triggers recorded in the proposal are met.
- No autonomous authority: merge, release, publish, force-push, and closeout
  stay human- or policy-gated throughout.

## Exit criteria

See the `exit_criteria` frontmatter. In short: the artifact class is
documented, typed, validated, inspectable, communicable, evaluated, and
dogfooded — with durable-run and scheduling work delivered only once their
prerequisites exist.
