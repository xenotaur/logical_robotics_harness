---
resolution: null
blocked_reason: null
blocked: false
id: WI-LRH-CHAIN-DEFAULTS-INCREMENT-2
title: Implement Increment 2 of PROP-LRH-CHAIN-DEFAULTS -- confirm_fixes_batch per-gate autopilot
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
  - WS-LRH-CHAIN-DEFAULTS
related_design:
  - project/design/proposals/proposed/lrh-chain-defaults/00_proposal.md
  - project/work_items/resolved/WI-REVIEW-ROUND-ESCALATION-GATE.md
depends_on:
  - WI-LRH-CHAIN-DEFAULTS-INCREMENT-1
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - implement_closeout_plan_autopilot
acceptance:
  - "confirm_fixes_batch's auto_unless_unusual predicate is defined from real Increment 1 session evidence, not an invented threshold -- cites at least the specific sessions/PRs whose confirm-fixes rounds informed the definition"
  - The predicate is gate-owned in /lrh-confirm-fixes's own SKILL.md/reference file, not a shared rule engine, per Decision 2
  - closeout_plan remains categorically excluded -- not implemented as an autopilot candidate under any circumstance, per DEC-DELIBERATE-CHAIN-INITIATION and PROP-LRH-CHAIN-DEFAULTS Decision 3
  - The per-gate autopilot flag lives in the same chain-defaults profile Increment 1 established, without duplicating its storage/staleness/override mechanics
  - lrh validate reports 0 errors
  - diff -r src/lrh/skills/lrh-confirm-fixes/ .claude/skills/lrh-confirm-fixes/ reports no differences
required_evidence:
  - manual_review
  - lrh_validate
  - test_new_python
artifacts_expected:
  - src/lrh/skills/lrh-confirm-fixes/SKILL.md
  - src/lrh/skills/lrh-confirm-fixes/references/confirm-fixes-workflow.md
  - src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md
  - .claude/skills/lrh-confirm-fixes/SKILL.md
  - .claude/skills/lrh-confirm-fixes/references/confirm-fixes-workflow.md
  - .claude/skills/lrh-confirm-fixes/references/round-cap-gate.md
---

# Implement Increment 2 of `PROP-LRH-CHAIN-DEFAULTS` -- `confirm_fixes_batch` per-gate autopilot

## Summary

Implements Increment 2 of `PROP-LRH-CHAIN-DEFAULTS`: the
`confirm_fixes_batch` per-gate autopilot flag, defined from real session
evidence gathered after `WI-LRH-CHAIN-DEFAULTS-INCREMENT-1` ships and sees
use — per the proposal's own Implementation Plan, which explicitly
sequences this increment behind evidence-gathering rather than an
invented threshold.

## Problem / Context

`PROP-LRH-CHAIN-DEFAULTS`'s "Steelmanned Defaults" section deliberately
left `confirm_fixes_batch`'s `auto_unless_unusual` predicate unresolved,
recording only a leaning (auto-continue only if every finding is
Clear-satisfied and none carries a P0/P1 severity badge) rather than a
locked decision — because Increment 2 needs real Increment 1 evidence to
steelman what "unusual" should mean for this specific gate, mirroring
`WI-REVIEW-ROUND-ESCALATION-GATE`'s own escalating-threshold precedent
(prove the mechanism narrow before widening it). This work item is
therefore blocked on `WI-LRH-CHAIN-DEFAULTS-INCREMENT-1` shipping and
producing that evidence, not just blocked administratively.

### Prior Art Check

#### Duplication search

- **In-repo:** No existing per-gate autopilot implementation for
  `/lrh-confirm-fixes`. `round-cap-gate.md`'s durable-state, human-gated
  escalation mechanism is the direct structural precedent this work item
  extends, not a duplicate — `confirm_fixes_batch` sits alongside it as a
  second, independent reduced-asking mechanism for the same skill.
- **Sibling repos:** None identified.
- **External libraries:** Not applicable.
- **Recommendation:** Proceed.

#### Demand search

- **Work items:** `WI-REVIEW-ROUND-ESCALATION-GATE` (resolved) is the
  precedent this work item's predicate design should match in rigor, not
  a duplicate — different mechanism, same gate.
- **Proposals:** `PROP-LRH-CHAIN-DEFAULTS` (proposed, PR #490/#499 merged)
  is the governing design.
- **Recommendation:** No existing artifact to close or link.

## Scope

Implement `confirm_fixes_batch`'s autopilot predicate for
`/lrh-confirm-fixes`, informed by real Increment 1 evidence. Out of
scope: any other per-gate autopilot flag, including `closeout_plan`,
which stays categorically excluded per governance, not merely
undecided.

## Required Changes

1. Gather and cite real `/lrh-confirm-fixes` round evidence produced
   after `WI-LRH-CHAIN-DEFAULTS-INCREMENT-1` ships — specific sessions or
   PRs whose findings inform the predicate definition, not a hypothetical.
2. Define `confirm_fixes_batch`'s `auto_unless_unusual` predicate in
   `/lrh-confirm-fixes`'s own `SKILL.md` or reference file, gate-owned per
   Decision 2 — not a shared rule engine.
3. Wire the flag into the same chain-defaults profile Increment 1
   established, reusing its storage/staleness/override mechanics rather
   than duplicating them.
4. Explicitly confirm in the implementation that `closeout_plan` is not
   touched or offered as a candidate anywhere in this change.
5. Mirror all `src/lrh/skills/` changes into `.claude/skills/` exactly.

## Non-Goals

- Does not implement `closeout_plan` autopilot under any framing —
  categorically excluded per `DEC-DELIBERATE-CHAIN-INITIATION` and
  `PROP-LRH-CHAIN-DEFAULTS` Decision 3; revisiting that requires its own
  explicit decision amendment, not inclusion here.
- Does not build a generic, reusable rule engine for future gates —
  `confirm_fixes_batch`'s predicate is specific to this one gate.
- Does not touch `chain_init_confirmation` or any Increment 1 mechanism
  beyond reusing its existing storage.

## Acceptance Criteria

- `confirm_fixes_batch`'s predicate is defined from real Increment 1
  session evidence, citing specific sessions/PRs
- The predicate is gate-owned, not a shared rule engine
- `closeout_plan` remains categorically excluded
- The flag reuses Increment 1's profile mechanics without duplication
- `lrh validate` reports 0 errors
- `.claude/` mirrors match `src/lrh/skills/` exactly

## Validation

- lrh validate
- New unit tests for the predicate logic
- Manual dogfooding: at least one `/lrh-confirm-fixes` round exercising
  the autopilot path and one exercising the "unusual" escape to a live ask

## Risk Notes

The primary risk is shipping a predicate that's too permissive — auto-
continuing on a batch that actually needed a human look would defeat the
purpose of `/lrh-confirm-fixes` existing at all. Any implementation
should be checked in both directions: a genuinely routine batch is
auto-continued, and a batch with any real ambiguity still asks.
