---
id: WS-LRH-CHAIN-DEFAULTS
kind: planning_node
title: Persisted Chain-Defaults Profile for LRH Skill Gates
status: proposed
stage: conceived
origin: follow_up
summary: >
  Governs delivery of PROP-LRH-CHAIN-DEFAULTS: a repo-level, git-tracked
  defaults profile that reduces repeated hand-typed answers across LRH's
  chain-running skill gates (completion/stop conditions, self-review
  preference, per-gate autopilot) without weakening the merge or
  chain-initiation gates.
related_design:
  - project/design/proposals/proposed/lrh-chain-defaults/00_proposal.md
  - project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md
  - project/memory/decisions/DEC-AGENT-EXECUTED-MERGE-GATE.md
  - project/work_items/resolved/WI-REVIEW-ROUND-ESCALATION-GATE.md
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
work_items:
  - WI-DEC-CHAIN-INIT-SKIP-AMENDMENT
  - WI-LRH-CHAIN-DEFAULTS-INCREMENT-1
  - WI-LRH-CHAIN-DEFAULTS-INCREMENT-2
exit_criteria:
  - A design-review session has produced concrete, steelmanned default values (completion condition, stop-work condition, self-review preference) with recorded rationale, before any Increment 1 code lands
  - Increment 1 (chain-level defaults: schema + propose-and-confirm flow wired into /lrh-land and /lrh-execute Step 2) implemented, lrh validate 0 errors, installed in both src/ and .claude/ mirrors
  - Increment 2 (per-gate autopilot: confirm_fixes_batch flag; closeout_plan is categorically excluded per DEC-DELIBERATE-CHAIN-INITIATION, see PROP-LRH-CHAIN-DEFAULTS Decision 3) implemented, lrh validate 0 errors, installed in both src/ and .claude/ mirrors, using Increment 1 session evidence to justify the gate's "unusual" predicate
  - PROP-LRH-CHAIN-DEFAULTS status updated to adopted
  - CLAUDE.md ## Skills index updated for any new or materially changed skill behavior
---

## Purpose

This workstream governs delivery of `PROP-LRH-CHAIN-DEFAULTS`: a
persisted, user-editable defaults profile that pre-fills the answers LRH's
chain-running skills currently re-derive from scratch at every invocation
(completion condition, stop-work condition, self-review-vs-bot-retrigger
preference) and, in a second increment, extends the same idea to per-gate
autopilot for `/lrh-confirm-fixes` and `/lrh-closeout`. It exists now
because the friction is compounding — this session alone restated the
self-review preference by hand across five separate `/lrh-land`
invocations — and because the design proposal explicitly requires a
steelmanning pass on concrete default values before any code is written,
which this workstream sequences as its first deliverable rather than
skipping.

## Scope

- Hold a dedicated design-review session to steelman concrete default
  values (completion condition, stop-work condition, self-review
  preference, and which gates if any start in `auto_unless_unusual`)
  before Increment 1 implementation begins.
- Implement Increment 1: chain-defaults profile schema, propose-and-confirm
  flow wired into `/lrh-land` and `/lrh-execute` Step 2, persistence for
  completion/stop-condition text and self-review preference.
- Implement Increment 2: per-gate autopilot flag (`confirm_fixes_batch`),
  with a gate-owned "unusual" predicate, informed by Increment 1 session
  evidence. `closeout_plan` is not an Increment 2 candidate —
  `/lrh-closeout`'s plan-confirm gate is categorically excluded from any
  autopilot tier per `DEC-DELIBERATE-CHAIN-INITIATION` (see
  `PROP-LRH-CHAIN-DEFAULTS` Decision 3).
- Adopt `PROP-LRH-CHAIN-DEFAULTS` once both increments are complete.

## Prior Art Check

### Duplication search
- In-repo: No existing chain-defaults-profile workstream.
  `WS-SKILLS-EXECUTE` governs the chain-running skills themselves
  (`/lrh-land`, `/lrh-execute`) but not a cross-cutting defaults
  mechanism; this workstream is a sibling, not an overlap.
- Sibling repos: None identified.
- External libraries: Not applicable.
- Recommendation: Proceed.

### Demand search
- Work items: None found requesting this workstream's scope directly.
- Proposals: `PROP-LRH-CHAIN-DEFAULTS` (proposed, PR #490) is the
  governing design — this workstream implements it.
- Backlog: No matching entries.
- Recommendation: No action; `PROP-LRH-CHAIN-DEFAULTS` is the demand item
  this workstream satisfies.

## Work Items

The design-review steelmanning session that produces concrete default
values has already happened (`PROP-LRH-CHAIN-DEFAULTS`'s "Steelmanned
Defaults" section, PR #499) and did not itself need a separate work
item.

- **WI-DEC-CHAIN-INIT-SKIP-AMENDMENT** — amend
  `DEC-DELIBERATE-CHAIN-INITIATION` to formally narrow its per-run
  live-reply requirement for `chain_init_confirmation: skip_if_opted_in`,
  per `PROP-LRH-CHAIN-DEFAULTS` Decision 6's own blocking Open Question.
  Produced `DEC-CHAIN-INIT-SKIP-CONSENT`.
- **WI-LRH-CHAIN-DEFAULTS-INCREMENT-1** — implement the chain-defaults
  profile schema, the propose-and-confirm flow at `/lrh-land`/`/lrh-execute`
  Step 2, and `chain_init_confirmation` in both modes. Depends on
  `WI-DEC-CHAIN-INIT-SKIP-AMENDMENT`.
- **WI-LRH-CHAIN-DEFAULTS-INCREMENT-2** — implement `confirm_fixes_batch`'s
  per-gate autopilot predicate, defined from real Increment 1 session
  evidence. Depends on `WI-LRH-CHAIN-DEFAULTS-INCREMENT-1`.

## Exit Criteria

- A design-review session has produced concrete, steelmanned default
  values (completion condition, stop-work condition, self-review
  preference) with recorded rationale, before any Increment 1 code lands
- Increment 1 implemented, `lrh validate` 0 errors, installed in both
  `src/` and `.claude/` mirrors
- Increment 2 implemented, `lrh validate` 0 errors, installed in both
  `src/` and `.claude/` mirrors, using Increment 1 session evidence to
  justify the `confirm_fixes_batch` gate's "unusual" predicate
- `PROP-LRH-CHAIN-DEFAULTS` status updated to `adopted`
- `CLAUDE.md ## Skills` index updated for any new or materially changed
  skill behavior

## Non-Goals

- Does not implement a generic, reusable rule engine across gates — each
  gate's "unusual" predicate stays gate-owned, per the proposal's Decision 2.
- Does not extend autopilot to the merge gate, the chain-initiation
  gate, or `/lrh-closeout`'s plan-confirm gate — all three stay
  categorically excluded, per the proposal's Decision 3 (amended during
  PR #490's review to add the closeout plan-confirm gate explicitly).
- Does not cover backends other than Claude.app and Codex Cloud.
- Does not skip or shortcut the design-review steelmanning session — it
  is a hard prerequisite to Increment 1, not an optional nicety.

## Relationship to Design

- Governing proposal: `project/design/proposals/proposed/lrh-chain-defaults/00_proposal.md`
- Governance decisions: `project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md`, `project/memory/decisions/DEC-AGENT-EXECUTED-MERGE-GATE.md`
- Precedent: `project/work_items/resolved/WI-REVIEW-ROUND-ESCALATION-GATE.md`
- Sibling workstream: `project/workstreams/proposed/WS-SKILLS-EXECUTE.md`

## Open Questions

- Exact scheduling/format of the design-review steelmanning session
  (synchronous conversation vs. a written proposal amendment) — deferred
  to when that work item is filed.
