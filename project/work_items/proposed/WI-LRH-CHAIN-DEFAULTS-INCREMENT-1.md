---
resolution: null
blocked_reason: null
blocked: false
id: WI-LRH-CHAIN-DEFAULTS-INCREMENT-1
title: Implement Increment 1 of PROP-LRH-CHAIN-DEFAULTS -- chain-level defaults profile
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
  - project/memory/decisions/DEC-CHAIN-INIT-SKIP-CONSENT.md
  - project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md
depends_on:
  - WI-DEC-CHAIN-INIT-SKIP-AMENDMENT
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - implement_confirm_fixes_batch_autopilot
acceptance:
  - The chain-defaults profile schema exists at project/config/chain-defaults.yaml (or the location Decision 1 ultimately specifies), storing completion condition, stop-work condition, and self-review preference as repo-level, git-tracked plain YAML
  - The propose-and-confirm flow is wired into /lrh-land and /lrh-execute Step 2, pre-filling stored values while still requiring one live confirming reply per run under always_confirm (the default)
  - chain_init_confirmation: skip_if_opted_in is implemented per all five numbered requirements in DEC-CHAIN-INIT-SKIP-CONSENT's Decision section -- initiation act preserved, two-step consent, user-local storage (never the shared profile), value-hash binding with invalidation on change, and the mandatory per-run special-conditions check
  - Decision 4's profile-update offer (a live instruction that diverges from a stored default is offered back as an update, never silently persisted) is implemented at the chain-authorization gate
  - Decision 5's staleness fallback (a stored default falls back to always_ask if the referenced gate's own skill logic has changed materially since confirmation) is implemented
  - confirm_fixes_batch and any other per-gate autopilot flag are explicitly out of scope for this work item -- Increment 2's responsibility
  - lrh validate reports 0 errors
  - diff -r src/lrh/skills/lrh-land/ .claude/skills/lrh-land/ and the /lrh-execute equivalent report no differences
required_evidence:
  - manual_review
  - lrh_validate
  - test_new_python
artifacts_expected:
  - project/config/chain-defaults.yaml
  - src/lrh/skills/lrh-land/SKILL.md
  - src/lrh/skills/lrh-land/references/land-workflow.md
  - src/lrh/skills/lrh-execute/SKILL.md
  - .claude/skills/lrh-land/SKILL.md
  - .claude/skills/lrh-land/references/land-workflow.md
  - .claude/skills/lrh-execute/SKILL.md
---

# Implement Increment 1 of `PROP-LRH-CHAIN-DEFAULTS` -- chain-level defaults profile

## Summary

Implements Increment 1 of `PROP-LRH-CHAIN-DEFAULTS`: the chain-defaults
profile schema, the propose-and-confirm flow at `/lrh-land`/`/lrh-execute`
Step 2, completion/stop-condition and self-review-preference persistence,
and the `chain_init_confirmation` liveness field (Decision 6, formalized
in `DEC-CHAIN-INIT-SKIP-CONSENT`). This is the first of two increments the
proposal's own Implementation Plan sequences; Increment 2 (per-gate
autopilot) is explicitly out of scope here and tracked as its own work
item.

## Problem / Context

`PROP-LRH-CHAIN-DEFAULTS` (PR #490) and its steelmanning amendment
(PR #499) fully specify the mechanism's shape and concrete default values,
but nothing has been implemented yet — `implementation_status:
not_started`. `DEC-CHAIN-INIT-SKIP-CONSENT` (this session) resolved the
one remaining blocker (`skip_if_opted_in`'s governance narrowing), so
Increment 1 is now unblocked in full.

### Prior Art Check

#### Duplication search

- **In-repo:** No existing implementation of any part of the chain-defaults
  mechanism. `round-cap-gate.md`'s durable-state pattern
  (`src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md`) is the
  closest structural precedent for the profile's file-based, gate-owned
  state model, not a duplicate.
- **Sibling repos:** None identified.
- **External libraries:** Not applicable.
- **Recommendation:** Proceed.

#### Demand search

- **Work items:** `WI-DEC-CHAIN-INIT-SKIP-AMENDMENT` (resolved via this
  session) is a direct dependency, not a duplicate — it produced the
  decision this work item's `skip_if_opted_in` requirement depends on.
- **Proposals:** `PROP-LRH-CHAIN-DEFAULTS` (proposed, PR #490 and #499
  merged) is the governing design this work item implements.
- **Recommendation:** No existing artifact to close or link; this work
  item is the direct response to that proposal's own Implementation Plan.

## Scope

Implement Increment 1 exactly as `PROP-LRH-CHAIN-DEFAULTS`'s
Implementation Plan and Steelmanned Defaults sections specify: the profile
schema and storage, the propose-and-confirm flow, and
`chain_init_confirmation` in both its modes. Out of scope: any per-gate
autopilot flag (`confirm_fixes_batch` or otherwise) — Increment 2's work.

## Required Changes

1. Define and implement the chain-defaults profile schema (repo-level,
   git-tracked plain YAML, per Decision 1) storing the completion
   condition, stop-work condition, and self-review preference defaults.
2. Wire the propose-and-confirm flow into `/lrh-land` and `/lrh-execute`
   Step 2: on first encounter, propose the steelmanned defaults from
   `PROP-LRH-CHAIN-DEFAULTS`; on subsequent runs, pre-fill stored values.
3. Implement `chain_init_confirmation: always_confirm | skip_if_opted_in`
   per `DEC-CHAIN-INIT-SKIP-CONSENT`'s Decision section in full — all five
   numbered requirements, not only the field's existence.
4. Implement Decision 4's profile-update offer at the end of a run where
   a live instruction diverged from the stored default.
5. Implement Decision 5's staleness fallback.
6. Mirror all `src/lrh/skills/` changes into `.claude/skills/` exactly.

## Non-Goals

- Does not implement `confirm_fixes_batch` or any other per-gate autopilot
  flag — Increment 2's own work item.
- Does not touch the merge gate or `/lrh-closeout`'s plan-confirm gate in
  any way — both remain categorically excluded per
  `DEC-CHAIN-INIT-SKIP-CONSENT`'s Scope section.
- Does not verify Codex Cloud plumbing beyond what's needed for this
  work item's own testing — `PROP-LRH-CHAIN-DEFAULTS`'s Open Question on
  that remains separately open.

## Acceptance Criteria

- The chain-defaults profile schema exists, storing completion condition,
  stop-work condition, and self-review preference as repo-level,
  git-tracked plain YAML
- The propose-and-confirm flow is wired into `/lrh-land` and
  `/lrh-execute` Step 2, pre-filling stored values while still requiring
  one live confirming reply per run under `always_confirm`
- `chain_init_confirmation: skip_if_opted_in` is implemented per all five
  numbered requirements in `DEC-CHAIN-INIT-SKIP-CONSENT`'s Decision
  section
- Decision 4's profile-update offer is implemented
- Decision 5's staleness fallback is implemented
- Per-gate autopilot is explicitly out of scope
- `lrh validate` reports 0 errors
- `.claude/` mirrors match `src/lrh/skills/` exactly

## Validation

- lrh validate
- New unit tests for the profile schema, the value-hash binding, and the
  special-conditions check
- Manual dogfooding: at least one `/lrh-land` run using `always_confirm`
  pre-filled defaults, and one exercising the `skip_if_opted_in` opt-in
  flow end to end

## Risk Notes

`skip_if_opted_in` is the highest-risk piece — an implementation that
gets the value-hash binding or the special-conditions check wrong would
silently reintroduce exactly the governance gap `DEC-CHAIN-INIT-SKIP-CONSENT`
was written to close narrowly. Any implementation must be checked against
that decision's five numbered requirements individually, not just against
whether the feature "works."
