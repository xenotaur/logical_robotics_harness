---
resolution: null
blocked_reason: null
blocked: false
id: WI-WORK-ITEM-BLOCKED-STATE-EXPRESSIVENESS
title: Let a proposed work item express that it is blocked, and by a non-work-item artifact
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
related_workstreams: []
related_design:
  - project/design/proposals/proposed/invocation-and-gate-reset/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - auto_resolve_existing_blocked_items
acceptance:
  - A proposed work item can express that it must not be started, and evaluate_prompt_readiness reports it as not prompt-ready
  - A work item can express a blocker that is not a work item -- a decision record, an external event, or a proposal -- without abusing blocked_by
  - lrh validate accepts the new expression and still rejects genuinely malformed blocked state
  - WI-LRH-CHAIN-DEFAULTS-INCREMENT-3 is migrated from its prose banner to the new mechanism and reports prompt_ready no
  - Existing work items are unaffected -- no currently-valid item becomes invalid, and no unblocked item becomes blocked
  - New and changed Python carries unit tests covering the proposed, active, and non-work-item-blocker cases
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_new_python
artifacts_expected:
  - src/lrh/control/work_item_policy.py
  - src/lrh/assist/work_item_prompt_core.py
  - src/lrh/control/validator.py
  - project/work_items/proposed/WI-LRH-CHAIN-DEFAULTS-INCREMENT-3.md
---

# Let a proposed work item express that it is blocked, and by a non-work-item artifact

## Summary

A `proposed` work item cannot currently record that it must not be started. The
combination of three independent rules leaves a genuine, occupied state with no
valid representation — and `evaluate_prompt_readiness` reports such an item as
ready, so a chain runner will select it and begin work the item itself forbids.

## Problem / Context

Three rules interact to close off the state:

1. **`blocked: true` requires `status: active`.**
   `src/lrh/control/work_item_policy.py:139-147` raises
   `WORK_ITEM_BLOCKED_STATUS_INVALID` ("blocked may only be true when status is
   'active'") otherwise. A `proposed` item therefore cannot be marked blocked at
   all.
2. **`blocked_by:` accepts only work-item IDs.**
   `src/lrh/control/validator.py:1502-1509` validates it against
   `set(work_item_map)`, emitting `UNKNOWN_BLOCKER` for anything else. A blocker
   that is a decision record, a design proposal, or an external event has no
   field.
3. **Readiness keys on `blocked`.**
   `src/lrh/assist/work_item_prompt_core.py:100-106`
   (`evaluate_prompt_readiness`) adds "work item is marked blocked" only when
   that flag is set. With rule 1 preventing the flag, a blocked-but-proposed
   item reports `prompt_ready: yes`.

### The live instance that surfaced it

`WI-LRH-CHAIN-DEFAULTS-INCREMENT-3` must not start until the DEC record from
`WS-INVOCATION-AND-GATE-RESET` Stage 3 narrows `PROP-LRH-CHAIN-DEFAULTS`
Decision 3. Its only declared dependency
(`WI-LRH-CHAIN-DEFAULTS-INCREMENT-1`) is already resolved, so it reports
`prompt_ready: yes`. Attempting to encode the truth failed on every available
field: `blocked: true` was rejected by rule 1, and the blocker is a decision
record, so rule 2 excluded `blocked_by:`. The constraint currently lives in a
prose banner in the body — which a human reads and a chain runner does not.

This is not a documentation problem. `/lrh-execute` resolves "the next ready WI
under a WS-ID", and `WS-LRH-CHAIN-DEFAULTS` owns that item, so the selection
path leads directly to work its own Risk Notes forbid.

### Why the existing rules are individually reasonable

Rule 1 plausibly exists to stop `blocked` being used as a backlog-parking
mechanism — an item nobody has started is not "blocked", it is merely proposed.
Rule 2 keeps `blocked_by:` a resolvable graph edge rather than free text. The
defect is emergent from their combination, so the fix should preserve both
intents rather than simply relaxing either.

### Prior Art Check

**Duplication search**

- In-repo: No work item, proposal, or backlog entry addresses blocked-state
  expressiveness or readiness selection. Keyword matches in
  `project/work_items/proposed/` are incidental (items that merely carry the
  fields). `project/design/backlog.md` has no entry.
  `WI-BOUNDED-STABILIZATION-LOOP-DESIGN` concerns loop bounding, not readiness.
- Sibling repos: None identified; this is LRH control-plane schema.
- External libraries: Not applicable.
- Recommendation: Proceed.

**Demand search**

- Work items: None requesting this.
- Proposals: `PROP-INVOCATION-AND-GATE-RESET` surfaced the instance but does not
  scope a fix; this work item is the follow-up.
- Backlog: No matching entries.
- Recommendation: No action; nothing to close.

## Scope

The blocked-state representation for work items and the readiness evaluation
that consumes it: `work_item_policy.py`'s validation rule,
`validator.py`'s `blocked_by` relation check, and
`work_item_prompt_core.py`'s `evaluate_prompt_readiness`. Plus migrating the one
known instance off its prose banner.

Out of scope: `/lrh-execute`'s selection algorithm itself (it should simply
respect whatever readiness reports), and the separate `execution_ready`
mechanism in `src/lrh/control/execution_readiness.py`, which is a different
gate.

## Required Changes

1. Choose and implement a representation. Three candidates, to be decided during
   design rather than pre-committed here:
   - Relax rule 1 to permit `blocked: true` on `proposed` items, keeping the
     mandatory non-empty `blocked_reason` that already accompanies it.
   - Add a distinct field (e.g. `blocked_by_artifact:` or `depends_on_artifact:`)
     accepting non-work-item references, validated against the artifact IDs the
     control plane already knows (`DEC-*`, `PROP-*`, `WS-*`).
   - Introduce an explicit `on_hold` status distinct from `blocked`, if the
     `blocked`-means-active intent is worth preserving strictly.
2. Make `evaluate_prompt_readiness` report not-ready for whichever
   representation is chosen, with a reason string naming the actual blocker.
3. Keep `lrh validate` rejecting genuinely malformed states — an unexplained
   block, or a reference to an artifact that does not exist.
4. Migrate `WI-LRH-CHAIN-DEFAULTS-INCREMENT-3` from its prose banner to the new
   mechanism, and delete the banner.
5. Add unit tests covering: proposed-and-blocked, active-and-blocked,
   blocked-by-a-decision-record, and the negative cases that must still fail.

## Non-Goals

- Does not change `/lrh-execute`'s selection logic. If readiness reports
  correctly, selection follows.
- Does not touch the `execution_ready` readiness mechanism, which answers a
  different question.
- Does not retroactively re-classify existing work items. No currently-valid
  item may become invalid, and no unblocked item may become blocked.
- Does not add a general dependency graph across artifact types. The narrow goal
  is expressing "do not start this yet, because X", not modelling arbitrary
  cross-artifact relationships.

## Acceptance Criteria

- A `proposed` work item can express that it must not be started, and
  `evaluate_prompt_readiness` reports it not prompt-ready.
- A work item can name a blocker that is not a work item — decision record,
  proposal, or external event — without abusing `blocked_by:`.
- `lrh validate` accepts the new expression and still rejects malformed blocked
  state.
- `WI-LRH-CHAIN-DEFAULTS-INCREMENT-3` is migrated off its prose banner and
  reports `prompt_ready: no`.
- No currently-valid work item becomes invalid; no unblocked item becomes
  blocked.
- New and changed Python carries unit tests for the proposed, active, and
  non-work-item-blocker cases.
- `lrh validate` reports 0 errors.

## Validation

- `lrh validate`
- `lrh work-items readiness WI-LRH-CHAIN-DEFAULTS-INCREMENT-3` reports `prompt_ready: no` with a reason naming the blocking artifact
- `scripts/test` (or the project's canonical Python test command) passes, including the new cases
- Regression check: `lrh work-items readiness` across all existing proposed work items produces the same verdicts as before this change, except the one deliberately migrated

## Risk Notes

The main risk is scope creep into a general cross-artifact dependency graph.
`blocked_by:` is deliberately a resolvable edge between work items; widening it
to arbitrary artifacts could turn readiness into a graph traversal with cycle
and staleness concerns it does not currently have. Prefer the narrowest
representation that makes the one real case expressible.

**Second, and the larger risk: `blocked` is read through at least five
independent sites, only one of which uses the typed model.** A change to its
semantics must land in all of them or the flag will mean different things to
different consumers. Verified directly:

| Site | How it reads `blocked` |
|---|---|
| `src/lrh/control/models.py:46` | the typed `WorkItem.blocked` field |
| `src/lrh/control/loader.py` | populates the typed field from frontmatter; feeds `core_state.py` → `serve.py` and `ux/dashboard.py` |
| `src/lrh/control/planning_tree.py:256` | `_frontmatter_bool(artifact.frontmatter, "blocked")` — recomputes, bypassing the typed field |
| `src/lrh/control/work_item_policy.py:126` | `metadata.get("blocked")` — validation |
| `src/lrh/assist/work_item_prompt_core.py:76` | `frontmatter.get("blocked")` — readiness |

`src/lrh/assist/snapshot_cli.py` consumes the `planning_tree.py` projection, so
it inherits the frontmatter-derived value rather than the typed one.

The practical consequence: validation, readiness, the planning tree, and the
dashboard each derive this flag separately. Introducing a new representation
that only some of them understand would produce an item that reads blocked in
one surface and ready in another — a worse failure than the current one, which
is at least consistent. Enumerate every consumer before choosing a
representation, and treat this table as a starting point rather than proof of
completeness.
