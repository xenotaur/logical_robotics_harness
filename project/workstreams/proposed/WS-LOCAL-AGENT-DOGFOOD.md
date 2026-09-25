---
id: WS-LOCAL-AGENT-DOGFOOD
kind: planning_node
title: "Local Agent Dogfood"
status: proposed
stage: assessed
origin: design_review
summary: "Measure useful local-agent workflows through isolated briefing and repository-investigation prototypes before expanding runtime authority."
parent_id: WS-EXECUTION-FRAMEWORK
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_design:
  - project/design/proposals/proposed/local-agent-dogfood/00_proposal.md
  - project/design/execution_framework_mvp.md
  - project/design/proposals/proposed/constitutional-sandbox-envelope/00_proposal.md
work_items:
  - WI-LOCAL-AGENT-001
  - WI-LOCAL-AGENT-002
exit_criteria:
  - "Stage 0 has a reproducible implementation, evaluation report, and human decision."
  - "Stage 1 is evaluated if authorized, or explicitly deferred or abandoned with rationale."
  - "A stop, revise, or promote decision cites measured usefulness and boundary checks."
  - "Private logs stay out of Git and production behavior remains unchanged."
  - "Any proposed next stage has separate scope and authority gates."
---

# Local Agent Dogfood

## Purpose

Find out whether a modest local model can reduce human effort on routine LRH and
LCATS work. Coordinate useful experiments while preserving the parent execution
framework's safe-default behavior. `stage: assessed` records a proposed direction;
the design is still under joint review and is not locked or selected for execution.

## Scope

Own the first two steps of the proposal: a static-context briefing assistant and
a bounded source investigator. Deliver one evolving temporary Python CLI,
exportable private attempt logs, durable sanitized experiment reports, and human
advancement decisions. The workstream closes on an evidence-backed decision,
including a negative result; it does not promise a complete agent product.

Prototype code belongs under `experimental/local_agent/`, outside the package
and default test discovery. The first leaf documents a durable `experiments/`
convention before adding numbered reports. Do not promote code during this lane.

## Prior Art Check

The proposal's Prior Art Check is the source-grounded comparison at main commit
`8603b6514329ea242294da420aa448d2fc959fd1`. Existing snapshots, readiness, and run
packets supply context; existing session/archive records supply later identity
links. `WS-EXECUTION-FRAMEWORK` owns production execution architecture;
`WS-LRH-ASSISTANTS` owns role artifacts and its own sequencing gates. The
constitutional sandbox envelope owns the future layered action-review design.

**Decision:** this is a child experiment, not a replacement parent workstream or
assistant-stage implementation. The existing Claude-only runtime proposal must
be reconciled before production local-runner adoption. Existing deterministic
tools remain evaluation baselines, consistent with the decision not to add a
standalone `/lrh-assess` skill.

## Work Items

| Item | Deliverable | Start condition |
| --- | --- | --- |
| `WI-LOCAL-AGENT-001` | Static-context briefing CLI, logs/export, and a measured pilot. | Design lane approved; owner selects model, hardware, safe corpus, and scoring thresholds. |
| `WI-LOCAL-AGENT-002` | Bounded read/search loop and comparison against stage 0. | 001 complete, findings reviewed, and human explicitly authorizes investigation. |

Stages 2–5 (patch drafting, guarded execution, session handoff, and local UI) are
roadmap hypotheses in the proposal, not executable leaves in this workstream.
Private/public hosting, model training, and distribution are later work.

## Exit Criteria

- Stage 0 has reproducible code, method, sanitized results, and a human decision.
- Stage 1 has equivalent evidence if selected; otherwise record why it is deferred
  or abandoned and reconcile its proposed leaf when closing this workstream.
- The owner chooses stop, revise, or promote based on actual human effort,
  groundedness, latency, and boundary behavior.
- Private logs remain private; package APIs, default serve behavior, and project
  status authority have not changed.
- Any next stage has a separate reviewed scope, safety contract, and work item.

## Non-Goals

No production runner, stable public API, MCP server, autonomous work selection,
command execution, patch application, assistant scheduling, public service,
fine-tuning, or production packaging. No automatic advancement on a green test
suite or a model-generated success claim.

## Dependencies and Review Gates

Merging this planning package does not activate either leaf. Adoption/selection
must explicitly allow the experimental lane while preserving canonical production
sequencing. References to existing focus/roadmap provide traceability, not a change
to current focus. No existing assistant blocker is cleared by this workstream.
