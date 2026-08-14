---
id: DEC-SINGLE-ASK-RUN-GATES
---

# Single-Ask Run Gates Preserve Gates While Collapsing Restatements

Status: accepted
Date: 2026-08-13

## Summary

Two lifecycle chains were asking the same question twice: the merge gate
followed by closeout, and `/lrh-execute`'s chain gate followed by
`/lrh-implement`'s plan gate. This decision amends
`DEC-DELIBERATE-CHAIN-INITIATION` on that narrow axis. A chain may collapse a
downstream restatement gate into an upstream gate when the upstream gate
presents the actual plan the human is approving, and the downstream step asks
again only on mechanical material divergence from that approved plan.

This is a single-ask change, not a no-ask change.

## Context

`PROP-INVOCATION-AND-GATE-RESET` Decision 7 chose the merge/closeout shape:
present the merge command together with the closeout plan; one live reply
authorizes both; merge happens first; closeout writes after the merge commit
exists. Decision 11 applies the same shape to the front of `/lrh-execute`:
derive the deterministic `/lrh-implement` setup before the chain gate, present
the run plan there, and make `/lrh-implement` Step 4 ask only if the live plan
differs materially.

The old governing text in `DEC-DELIBERATE-CHAIN-INITIATION` said chain
initiation never satisfies a skill's internal confirmation gate. That remains
correct for unrelated or independently load-bearing gates, but it is too broad
for restatement gates whose content has already been approved in the same
chain.

## Decision

Single-ask run gates are permitted under these rules:

1. **The upstream gate must present the concrete downstream plan.** It is not
   enough to say "I will run the next skill." The gate must show the fields the
   downstream gate would ask about.
2. **The downstream step must compare mechanically.** If the live downstream
   plan matches the approved plan, the downstream gate is satisfied. If a
   material field differs, the downstream step asks again with a structured
   diff.
3. **Material divergence is field-based, not vibes-based.** For the
   `/lrh-execute` front-of-run collapse, material fields are the task summary's
   meaning, prompt ID, branch name, expected file changes, validation commands,
   readiness warnings, prior-art warnings, forbidden actions, and related
   workstream.
4. **Direct invocation is unaffected.** `/lrh-implement` invoked directly,
   especially on a free-form ad-hoc description, still asks its normal Step 4
   plan-confirm gate because no static work item was front-loaded into an
   approved run plan.
5. **Protected human/policy gates remain protected.** Merge authorization still
   follows `DEC-AGENT-EXECUTED-MERGE-GATE`; closeout still writes only after the
   merged PR state is verified; publish and release gates are unaffected.

## Consequences

- `/lrh-execute` hoists `/lrh-implement` Steps 1, 1.5, 2, and 3 before its
  chain gate and presents their outputs as an approved run plan.
- `/lrh-implement` Step 4 becomes divergence-only when, and only when, it is
  reached through `/lrh-execute` with an approved run plan.
- Decision 7's merge/closeout collapse and Decision 11's front-of-run collapse
  are the same governance pattern: ask once with the actual plan, then alert on
  new facts instead of asking a restated question.

## Non-Goals

- Does not activate `chain_init_confirmation: skip_if_opted_in`.
- Does not allow timeout-and-proceed on any gate.
- Does not remove `/lrh-land`'s chain gate or merge gate.
- Does not weaken explicit, in-session merge authorization.
