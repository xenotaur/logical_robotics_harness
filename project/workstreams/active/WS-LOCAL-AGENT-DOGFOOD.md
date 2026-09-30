---
id: WS-LOCAL-AGENT-DOGFOOD
kind: planning_node
title: "Local Agent Dogfood"
status: active
stage: executing
origin: design_review
summary: "Build a ladder of small, usable local-model toys (ask, brief, look around), judged by the owner from automatic run logs before expanding authority."
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
  - "T0 ask and T1 brief are usable, have been used on real work, and have an owner stop, revise, or proceed decision informed by their log summary."
  - "T2 look-around is built and decided on if authorized, or explicitly deferred or abandoned with rationale."
  - "Any toy with tools has passing automated dispatch-boundary tests."
  - "Private logs stay out of Git and production behavior remains unchanged."
  - "Any proposed next toy has separate scope and authority gates; toys from T4 use the proposal's safety design."
  - "Deferred follow-ups from experimental PRs are reviewed and resolved or carried forward."
---

# Local Agent Dogfood

## Purpose

Find out whether a modest local model is useful enough on routine LRH and LCATS
work that the owner keeps reaching for it, by building small, usable toys and
using them. Coordinate the toys while preserving the parent execution
framework's safe-default behavior. On 2026-09-29 the owner approved the toy
ladder for T0 and T1 (the proposal's "Toy Ladder Approval" section), replacing
the earlier stage-0 pilot; `stage: executing` reflects `WI-LOCAL-AGENT-001`. The
long-term design remains a proposal under joint review, and T2 is not selected.

## Scope

Own the read-only rungs of the proposal's toy ladder: T0 ask, T1 brief, and T2
look-around. Deliver one evolving temporary Python CLI with automatic private run
logs, one-key ratings, log summaries, and the owner's decision at each rung. The
workstream closes on those decisions, including a decision to stop; it does not
promise a complete agent product.

Prototype code belongs under `experimental/local_agent/`, outside the package
and default test discovery. Optional durable write-ups go in numbered
`experiments/` directories. Do not promote code during this lane. PRs confined to
`experimental/` and execution records use the proposal's lighter Experimental PR
Process; everything else uses the normal process.

## Prior Art Check

The proposal's Prior Art Check is the source-grounded comparison at main commit
`8603b6514329ea242294da420aa448d2fc959fd1`. Existing snapshots, readiness, and run
packets supply context; existing session/archive records supply later identity
links. `WS-EXECUTION-FRAMEWORK` owns production execution architecture;
`WS-LRH-ASSISTANTS` owns role artifacts and its own sequencing gates. The
constitutional sandbox envelope owns the future layered action-review design.

**Decision:** this is a child experiment, not a replacement parent workstream or
assistant-stage implementation. The existing Claude-only runtime proposal must
be reconciled before production local-runner adoption, consistent with the
decision not to add a standalone `/lrh-assess` skill.

## Work Items

| Item | Deliverable | Start condition |
| --- | --- | --- |
| `WI-LOCAL-AGENT-001` | T0 ask and T1 brief: usable commands with automatic logging, ratings, and log summaries. | Active; toy ladder approved 2026-09-29. |
| `WI-LOCAL-AGENT-002` | T2 look-around: a capped, read-only tool loop over tracked files, with automated boundary tests. | T0/T1 used and the owner explicitly authorizes read/search tools. |

T3 and later toys (suggest a patch, execute under guardrails, session handoff,
local workbench) are roadmap hypotheses in the proposal, not executable leaves in
this workstream. Private/public hosting, model training, and distribution are
later work.

## Exit Criteria

- T0 and T1 are usable, used on real work, and decided on by the owner from their
  log summary and experience.
- T2 is built and decided on if selected; otherwise record why it is deferred or
  abandoned and reconcile its proposed leaf when closing this workstream.
- Any toy with tools has passing automated dispatch-boundary tests.
- Private logs remain private; package APIs, default serve behavior, and project
  status authority have not changed.
- Any next toy has a separate reviewed scope and work item; from T4, the
  proposal's safety design applies.
- Deferred follow-ups from experimental PRs are reviewed, then resolved or
  carried forward.

## Non-Goals

No production runner, stable public API, MCP server, autonomous work selection,
command execution, patch application, assistant scheduling, public service,
fine-tuning, or production packaging. No formal pre-registered study, manual
timing, or hand-written baselines for the read-only toys. No automatic
advancement on a green test suite or a model-generated success claim.

## Dependencies and Review Gates

The toy-ladder approval is recorded in the proposal's "Toy Ladder Approval"
section, and the canonical focus and execution-framework documents describe this
lane as adjacent experimental work that preserves production sequencing.
`WI-LOCAL-AGENT-002` remains proposed and needs its own owner decision after T0
and T1 have been used. References to existing focus/roadmap provide
traceability, not a change to current focus. No existing assistant blocker is
cleared by this workstream.
