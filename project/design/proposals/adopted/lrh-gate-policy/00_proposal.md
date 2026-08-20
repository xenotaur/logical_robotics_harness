---
id: PROP-LRH-GATE-POLICY
type: design_proposal
title: LRH Gate Policy
status: adopted
implementation_status: implemented
created_on: 2026-08-20
updated_on: 2026-08-20
implemented_by:
  - WI-GATE-POLICY-CASCADE-STAGE3
related_design:
  - project/design/proposals/proposed/invocation-and-gate-reset/00_proposal.md
  - project/design/proposals/proposed/lrh-chain-defaults/00_proposal.md
  - project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md
  - project/memory/decisions/DEC-CHAIN-INIT-SKIP-CONSENT.md
  - project/memory/decisions/DEC-AGENT-EXECUTED-MERGE-GATE.md
  - project/memory/decisions/DEC-SINGLE-ASK-RUN-GATES.md
  - project/memory/decisions/DEC-SELF-REVIEW-RECURSION-GUARD.md
supersedes: []
superseded_by: null
---

# LRH Gate Policy

## Summary

LRH gates protect decisions that still need human judgment. A gate should ask
once, with the actual decision payload visible; it should not ask again merely
to restate the same information. When a later step learns a genuinely new fact
or detects material divergence from what was approved, that step alerts and asks
again.

This proposal records the canonical gate model produced by
`WI-GATE-POLICY-CASCADE-STAGE3`. It replaces the accreted mix of per-skill
confirm prose, chain-defaults mechanics, and historical review-bot retrigger
language with one policy that skills can cite.

## Design Decisions

### Decision 1: Gate Assertions Are Statement-Shaped

Gate-policy cascade decisions are made by statement meaning, not artifact class.
A historical execution record or resolved work item may still contain narrative
about what happened. That narrative remains immutable. But a sentence in any
artifact that asserts current state about a still-live policy, work item,
workstream, skill, or decision must be corrected or explicitly superseded when
it becomes false.

### Decision 2: Chain Initiation Is Human-Initiated

A chain starts only from a deliberate human invocation and only with completion
and stop-work conditions supplied or signed off. The default
`chain_init_confirmation: always_confirm` path requires a fresh live reply for
those conditions on each run.

`chain_init_confirmation: skip_if_opted_in` remains a later activation path, not
the shipped default. It may skip only the condition-confirmation reply, only
under `DEC-CHAIN-INIT-SKIP-CONSENT`'s user-local, value-bound, revocable consent
model, and only when special-condition checks do not fire.

### Decision 3: Restatement Gates Collapse by Contract

If an upstream gate presents the concrete downstream plan, a downstream gate may
be satisfied by a mechanical no-material-divergence check against that approved
plan. If a material field differs, the downstream step asks again with a
structured diff.

This is the shared model for `/lrh-execute`'s front-of-run collapse and
`/lrh-land`'s merge-plus-closeout shape. It is single-ask, not no-ask.

### Decision 4: Protected Gates Remain Protected

Merge authorization still requires a fresh live reply to a SHA-locked merge
command. Publish and release gates are unaffected. `/lrh-closeout` still writes
only an approved closeout plan after merge state has been verified. Any active
assistant role policy that imposes a stricter merge prohibition or
human-executed-merge obligation overrides the general default.

### Decision 5: Review Stabilization Uses Substitute Self-Review, Not Manual Bot Retriggers

Manual hosted GitHub review-bot retriggering is retired from LRH skills. When a
fresh review signal is needed after normal automatic review surfaces are
exhausted, the substitute signal is `/lrh-self-review` in PR mode. Consecutive
substitute rounds that make no progress are bounded by the provisional
no-progress cap until Stage 4 replaces that mechanism.

### Decision 6: Gate Staleness Watches Gate Definitions

Stored chain-default confirmations become stale when gate-definition statements
change, not merely when an arbitrary watched file has a typo fix. Until LRH has
a parser for gate-definition sections, the operational check is conservative:
watch the files that carry gate-definition statements, then inspect the diff for
changes to the named gates before trusting stored consent.

Gate-definition statements are statements that define:

- when a gate is reached;
- what decision payload is presented;
- what reply or stored consent satisfies the gate;
- what special condition forces a live gate;
- what downstream step can rely on the gate;
- what action is forbidden without that gate.

### Decision 7: Stage 3.5 Uses the Human-Initiated Invocation Evidence Control

The named compensating control for Stage 3.5 is
`human_initiated_invocation_evidence`.

Before `chain_init_confirmation: skip_if_opted_in` may be activated for a run,
the executing skill must verify and record all of the following:

- the run began from a live user message that explicitly invoked the chain skill
  and named the target PR, WI, or WS;
- the run target resolved to the same PR, WI, or WS that the user named;
- no model-initiated `Skill()` call or sibling skill handoff is being treated as
  the human initiation act;
- local skip consent exists and is bound to the exact current
  `project/config/chain-defaults.yaml` blob hash;
- no special condition from `DEC-CHAIN-INIT-SKIP-CONSENT` fired.

The evidence can be a displayed gate preflight plus an execution-record or
run-journal note naming the user message, resolved target, profile hash, and
special-condition result. If any element is unavailable, Stage 3.5 must use
`always_confirm` for that run.

## Prior Art Check

### Duplication search

- In-repo: `PROP-INVOCATION-AND-GATE-RESET` specifies the Stage 3 need;
  `DEC-SINGLE-ASK-RUN-GATES` already covers one subset of the gate policy.
  No existing proposal records the complete gate policy, cascade taxonomy,
  staleness redesign, and Stage 3.5 compensating control together.
- Sibling repos: Taurcode has related `:execute` and `:land` prompts, but LRH
  planning artifacts do not govern that repository.
- External libraries: None identified; this is repository governance.
- Recommendation: Proceed.

### Demand search

- Work items: `WI-GATE-POLICY-CASCADE-STAGE3` explicitly requests this policy.
- Proposals: `PROP-INVOCATION-AND-GATE-RESET` Decisions 6, 7, 9, and 11 require
  it.
- Backlog: No separate backlog entry owns the full policy.
- Recommendation: Satisfy through `WI-GATE-POLICY-CASCADE-STAGE3`.

## Consequences

- Skills should cite this policy when deciding whether a gate must ask, can rely
  on an earlier approved run plan, or must alert on divergence.
- The chain-defaults staleness check watches gate-definition surfaces rather
  than only the original chain-runner files.
- Stage 3.5 remains blocked until the activation work item verifies
  `human_initiated_invocation_evidence`; this proposal defines the control but
  does not activate skip mode.
- Historical narrative remains untouched, but false present-tense claims about
  live artifacts are corrected even when they appear in resolved artifacts.
