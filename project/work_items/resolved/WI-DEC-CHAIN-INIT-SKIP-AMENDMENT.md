---
resolution: Implemented and merged in PR #507 (commit 7d44941) as DEC-CHAIN-INIT-SKIP-CONSENT
blocked_reason: null
blocked: false
id: WI-DEC-CHAIN-INIT-SKIP-AMENDMENT
title: Amend DEC-DELIBERATE-CHAIN-INITIATION to narrow the per-run live-reply requirement for opted-in skip mode
type: deliverable
status: resolved
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
  - project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md
  - project/memory/decisions/DEC-AGENT-EXECUTED-MERGE-GATE.md
  - project/design/proposals/proposed/lrh-chain-defaults/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - implement_skip_if_opted_in
acceptance:
  - A dated entry lands in project/memory/decision_log.md before being promoted, per design.md's decision-record tiers
  - New promoted decision-log entry exists, explicitly scoped to narrowing only the per-run live-reply requirement for a user-local, value-bound, revocable skip_if_opted_in consent -- not a general loosening of chain-initiation
  - DEC-DELIBERATE-CHAIN-INITIATION.md cross-references the new entry, following the precedent already set by its own DEC-AGENT-EXECUTED-MERGE-GATE cross-reference
  - WI-DEC-CHAIN-INIT-SKIP-AMENDMENT is registered in WS-LRH-CHAIN-DEFAULTS's work_items list, not only declared as related
  - The entry explicitly preserves the human's slash-command invocation as the deliberate initiation act, the mandatory per-run special-conditions check surviving skip mode, and the two-separate-affirmative-actions requirement (store defaults, then separately opt into skipping)
  - PROP-LRH-CHAIN-DEFAULTS's Open Question blocking skip_if_opted_in is updated to reference the new decision once it lands
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - project/memory/decision_log.md
  - project/memory/decisions/DEC-CHAIN-INIT-SKIP-CONSENT.md
  - project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md
  - project/design/proposals/proposed/lrh-chain-defaults/00_proposal.md
  - project/workstreams/active/WS-LRH-CHAIN-DEFAULTS.md
---

# Amend `DEC-DELIBERATE-CHAIN-INITIATION` to narrow the per-run live-reply requirement for opted-in skip mode

## Summary

`PROP-LRH-CHAIN-DEFAULTS`'s Decision 6 introduces
`chain_init_confirmation: skip_if_opted_in` — a user-local, value-bound,
revocable consent that lets
a chain-authorization gate skip re-confirming pre-filled completion/stop
conditions on runs where the user has separately opted in. During that
proposal's own review (PR #499), a Codex finding confirmed this genuinely
narrows `DEC-DELIBERATE-CHAIN-INITIATION`'s requirement that a human
"provided or signed off on" both conditions for *each* chain run — it is
not, as the proposal's first draft claimed, unaffected. This work item
formalizes that narrowing as its own decision-log entry, per
`DEC-DELIBERATE-CHAIN-INITIATION`'s own precedent
(`DEC-AGENT-EXECUTED-MERGE-GATE` narrowed the same decision's
merge-execution assumption via a dedicated entry, not a silent
proposal-level assertion).

## Problem / Context

`DEC-DELIBERATE-CHAIN-INITIATION.md:57-64` states: "An automatic chain
that follows those links may run, but only when a human has explicitly
initiated it and has provided or signed off on two conditions... Absent
an explicit initiation carrying both conditions, no chain self-starts."

`skip_if_opted_in` mode has no fresh live reply carrying those conditions
for the specific run in question — the human's slash-command invocation is
still a deliberate act, but it is not the same act the decision names.
`PROP-LRH-CHAIN-DEFAULTS` (PR #499) is explicit that this proposal alone
cannot resolve the gap: its Open Questions section blocks
`skip_if_opted_in` from shipping in any Increment 1 implementation until
this amendment lands. `always_confirm` mode (pre-filled text, still
requiring a live reply) has no such gap and is unblocked.

### Prior Art Check

#### Duplication search

- **In-repo:** No existing decision-log entry narrows
  `DEC-DELIBERATE-CHAIN-INITIATION`'s per-run live-reply requirement.
  `DEC-AGENT-EXECUTED-MERGE-GATE` narrowed the same governing decision, but
  on a different axis entirely (who executes the merge command, not
  whether a live reply is required) — not a duplicate, but the direct
  structural precedent this WI follows.
- **Sibling repos:** Not applicable — specific to this project's own
  chain-authorization governance.
- **External libraries:** Not applicable.
- **Recommendation:** Proceed.

#### Demand search

- **Work items:** None found requesting this specific amendment.
- **Proposals:** `PROP-LRH-CHAIN-DEFAULTS` (proposed, PR #499 merged) is
  the demand source — its own Open Questions section names this
  amendment as a hard prerequisite for `skip_if_opted_in`.
- **Recommendation:** No existing artifact to close or link; this WI is
  the direct response to that proposal's own blocking note.

## Scope

Author a new, narrowly-scoped decision-log entry that amends
`DEC-DELIBERATE-CHAIN-INITIATION` on exactly one axis: whether a fresh
live reply carrying the completion/stop conditions is required on every
chain-authorization gate, when a user has opted into `skip_if_opted_in`
mode for pre-filled, user-local, value-bound consent. Out of scope: any
other narrowing of that decision, any change to the merge gate
(`DEC-AGENT-EXECUTED-MERGE-GATE` is unaffected), and implementing the
`chain_init_confirmation` mechanism itself (that is Increment 1
implementation work, tracked separately under `WS-LRH-CHAIN-DEFAULTS`).

## Required Changes

1. Add a dated entry to `project/memory/decision_log.md` first — per
   `project/design/design.md`'s "Decision-record tiers" (`decision_log.md`
   is "the default landing spot... this is where every decision
   starts"), then promote it into `project/memory/decisions/DEC-CHAIN-INIT-SKIP-CONSENT.md`
   (or an equivalently precise ID), following
   `DEC-AGENT-EXECUTED-MERGE-GATE.md`'s structure (Summary, Context,
   Decision, Rationale, Alternatives considered, Consequences, Revisit
   conditions) — mirroring how the `DEC-AGENT-EXECUTED-MERGE-GATE`
   precedent itself updated both records, not the promoted file alone.
2. The entry must explicitly preserve, not silently drop:
   - The human's slash-command invocation as the deliberate initiation
     act in every mode.
   - The mandatory per-run "special conditions" check (unmet
     `depends_on`, prior failed/stopped run, uncommitted stray changes,
     mismatched target) that forces a live gate even in skip mode.
   - The two-separate-affirmative-actions requirement: storing default
     values never implies consent to skip confirming them; a distinct
     opt-in is required.
   - User-local scope for the skip consent (never the shared,
     git-tracked `project/config/chain-defaults.yaml` profile) and
     binding to a hash of the specific condition values it was granted
     against.
3. Update `DEC-DELIBERATE-CHAIN-INITIATION.md` to cross-reference the new
   entry, mirroring its existing `DEC-AGENT-EXECUTED-MERGE-GATE`
   cross-reference in both its "Revisit conditions" and "Consequences"
   sections.
4. Update `PROP-LRH-CHAIN-DEFAULTS`'s Open Question blocking
   `skip_if_opted_in` to reference the new decision by ID once it lands.

## Non-Goals

- Does not implement `chain_init_confirmation` or any other part of the
  `chain-defaults` profile mechanism — decision-log amendment only.
- Does not narrow `DEC-DELIBERATE-CHAIN-INITIATION` on any axis beyond
  the specific per-run live-reply question this WI scopes.
- Does not touch `DEC-AGENT-EXECUTED-MERGE-GATE` or the merge gate in
  any way.
- Does not authorize `skip_if_opted_in` to ship — it only removes the
  blocking Open Question; shipping still requires the Increment 1
  implementation work item this WI does not create.

## Acceptance Criteria

- A dated entry lands in `project/memory/decision_log.md` before being
  promoted, per `design.md`'s decision-record tiers
- New promoted decision-log entry exists, explicitly scoped to
  narrowing only the per-run live-reply requirement for a user-local,
  value-bound, revocable `skip_if_opted_in` consent — not a general
  loosening of chain-initiation
- `DEC-DELIBERATE-CHAIN-INITIATION.md` cross-references the new entry,
  following the precedent already set by its own
  `DEC-AGENT-EXECUTED-MERGE-GATE` cross-reference
- `WI-DEC-CHAIN-INIT-SKIP-AMENDMENT` is registered in
  `WS-LRH-CHAIN-DEFAULTS`'s `work_items` list, not only declared as
  related
- The entry explicitly preserves the human's slash-command invocation as
  the deliberate initiation act, the mandatory per-run
  special-conditions check surviving skip mode, and the
  two-separate-affirmative-actions requirement
- `PROP-LRH-CHAIN-DEFAULTS`'s Open Question blocking `skip_if_opted_in`
  is updated to reference the new decision once it lands
- `lrh validate` reports 0 errors

## Validation

- lrh validate
- Manual review confirming the new entry does not silently widen scope
  beyond the one axis this WI names

## Risk Notes

The primary risk is scope creep: an amendment framed broadly enough to
cover "any future autopilot expansion" would repeat the exact mistake
this WI exists to fix (a proposal-level claim of no impact that turned
out to be false, then a correction that must itself stay narrowly
scoped). Any implementation of this WI should be checked against
whether it grants anything beyond the specific `skip_if_opted_in`
consent model `PROP-LRH-CHAIN-DEFAULTS` Decision 6 already defines.
