---
id: PROP-LRH-MULTI-FOCUS-SUPPORT
type: design_proposal
title: "Focus Model Gaps and Multi-Focus Support: Options and Recommendation"
status: proposed
created_on: 2026-10-11
updated_on: 2026-10-11
implementation_status: not_started
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - project/design/design.md
  - project/context/humans.md
  - project/memory/decisions/precedence_semantics.md
  - src/lrh/control/loader.py
  - src/lrh/control/validator.py
  - src/lrh/core_state.py
  - src/lrh/control_plane/precedence.py
  - src/lrh/assist/snapshot_cli.py
  - src/lrh/serve.py
---

# Focus Model Gaps and Multi-Focus Support

## Summary

LRH supports exactly one focus, and that single-focus model is only partly
implemented: focus status is inconsistent, "active leaf" is defined twice, the
precedence resolver has no production caller, and `lrh serve` shows almost
nothing about foci. This proposal recommends first closing those gaps and
adding a read-only focus registry, with several simultaneously active foci
deferred until that baseline proves insufficient.

## Background / Motivation

A downstream project (LCATS) runs two or three concurrent threads (a Worldcon
presentation/paper wrap-up including the Heinlein detector, and a 1.0 release
with sidecar loading, PyPI, corpus cleaning and gutenbergpy replacement). Its
`current_focus.md` was stale for the new thread, so new work items were created
without focus links. Two needs are entangled: (N1) draft and validate a next
focus before activating it, and (N2) run several threads concurrently. The
originating handoff addressed N1 only.

Investigation against `main` (50f00813) showed the handoff's premise was right
on the loader and validator but overstated focus's reach, and that the real
cost of a stale or mismatched focus is silent under-reporting rather than an
error (see Current-State Gaps). `design.md:438` and `humans.md:431` both state
the model as singular ("only one focus should be active at a time").

## Prior Art Check

### Duplication search
- In-repo: No existing implementation found. Adjacent: PROP-LRH-OPEN-WORK
  (audits focus staleness, does not change the model).
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed

### Demand search
- Work items: None found
- Proposals: None found
- Backlog: No matching entries
- Recommendation: No action

## Current-State Gaps

All cites are against `main` at 50f00813 (line numbers were re-verified after
syncing; the cited source files are unchanged since 979ac1e0). Behavior marked
"ran" was reproduced on a scratch copy of `project/`.

**G1. "Active leaf" is defined twice, and one definition is gated on focus.**
`planning_tree.py:510` marks a work item an active leaf when it is `active`
with no children. `core_state.py:674-676` additionally requires
`is_current_focus_related`, computed at `core_state.py:642-647` against the
single loaded focus id. The serve payload emits both: `active_leaf_ids`
(`serve.py:864`, ungated) and `active_leaves` (`serve.py:865`, gated through
`active_leaf_work_items`, `core_state.py:410`). The HTML active-leaves list
(`serve.py:466`) and the card's active-work count (`dashboard.py:386`) use the
gated one. Active work not linked to the current focus is therefore dropped
from those views without any diagnostic, and the two fields can disagree.

**G2. Focus status means different things in different places.**
`FOCUS_STATUS` allows six values (`validator.py:26`) but nothing ties status to
location or requires `current_focus.md` to be `active` (the archived
`FOCUS-BOOTSTRAP` is itself `status: active`). `core_state.py:642` ignores
status entirely (ran: a paused current focus still reports the same focus and
active leaves). `precedence.py:89` treats a non-active focus as no focus, and
with no focus `precedence.py:117` puts every work item in scope. "Pause the
focus" therefore widens the resolver's scope while the dashboard still treats
that focus as current.

**G3. The precedence resolver has no production caller.**
`resolve_precedence` is re-exported (`control_plane/__init__.py:8`) and covered
by `tests/control_plane_tests/precedence_test.py`, but nothing under `src/`
calls it. The documented behavior that focus "determines which work items are
relevant" (`humans.md:435-437`) is enforced in practice only by one opt-in
snapshot scope and the G1 gate.

**G4. Focus filtering in snapshots is limited to one explicit scope.**
Only `lrh snapshot current_focus` filters by focus (`snapshot_cli.py:746-753`,
dispatch `:924`, filter `:607-632`); `project` and `work_item` scopes include
the focus summary but do not filter (`:721`, `:866`). The focus scope silently
falls back to all items when none match (`:629-632`) and hard-fails when
`current_focus.md` is missing (`:749-751`).

**G5. "No focus" is not a supported project state.**
Work items without `related_focus` are fine (optional; `work_items/audit.py:236`
warns only when an item has no roadmap/focus/design/workstream link). A
project without `current_focus.md` is not: the validator raises `FILE_NOT_FOUND`
(`validator.py:622-630`), any non-dependency-map error blanks core state
(`core_state.py:401`, `:448-460`), and `loader.py:36` reads the file
unconditionally. In the scratch run, removing the file produced an empty state
(0 work items) in `lrh serve`; that run also had 77 dangling `related_focus`
errors from this repo's own links, so the single-error blanking effect is
established by the code path, not isolated empirically.

**G6. `lrh serve` and the desktop app expose almost no focus information.**
The viewer shows one overview line (`serve.py:458-461,515`); the JSON payload
carries the current focus (`serve.py:845,3312-3324`) and per-item
`related_focus` / `is_current_focus_related` (`serve.py:3383,3391`), neither
rendered in HTML; the meta-dashboard card shows a "Focus:" string
(`dashboard.py:377`, `serve.py:2185`). There is no focus list, no work items
grouped by focus, and no view of archived foci (the loader never reads the
archive). Workstreams, by contrast, get a list and detail page
(`serve.py:1411-1447`). The desktop app (`apps/desktop`, Tauri) is a shell that
owns and displays `lrh serve` (`src-tauri/src/lib.rs:4`); its only focus
dependency is requiring a `project/focus` directory to recognize a workspace
(`settings.rs:141,182`, mirroring `loader.py:28`).

**G7. Archived foci are validated but unusable.**
The validator accepts ids from `focus/archive/**/*.md` for `related_focus`
(`validator.py:380-394`, `:1603-1611`) regardless of their status, but the
loader and core state never load them, so a `proposed` focus can exist only by
being misfiled in `archive/`.

## Options

Each option is assessed against the baseline above.

### Option (a): Single current focus plus `focus/proposed/` (N1)
Add a validated location for drafted-but-inactive foci.
- Pros: smallest code change; fixes G7; keeps the singular model that
  `design.md:438` and `humans.md:431` describe; proposed foci stay out of the
  precedence chain (`precedence.py:89`), so no change to the precedence decision.
- Cons: does not address N2; LCATS still has to choose one thread as current.
- Touch points: `validator.py:380-381` (glob), `loader.py:36,54` and
  `models.py:126` (read-only registry field), `design.md:438`.

### Option (b): Several active foci with a designated primary (N2)
- Pros: matches how projects actually run; makes "focus = filter" literal.
- Cons: largest blast radius; contradicts `humans.md:431`; requires a tie-break
  rule between foci and an update to the precedence decision (see below);
  compounds G1-G3 if built before they are fixed.
- Touch points: `loader.py:36,54`; `models.py:126,136`;
  `core_state.py:179-193,407,642-676`; `serve.py:845,3312`; `dashboard.py:377`;
  `snapshot_cli.py:597-632,721,746-790`; `precedence.py:9-12,31-35,79-107`;
  tests; the `snapshot current_focus` scope name.

### Option (c): Leave the model alone; document paused-focus plus archive swap
- Pros: no code.
- Cons: disqualified as written, because pausing the focus has opposite effects
  in the resolver and core state (G2) and the swap requires misfiling in
  `archive/` (G7). Becomes viable only after G2 is fixed.

### Option (d): One umbrella focus; threads are workstreams
Express LCATS-style threads as workstreams (already carrying `related_focus`,
`core_state.py:626`) under one focus with several priorities.
- Pros: zero schema change; fits the "priorities inside one focus" convention.
- Cons: relies on discipline; with G1 unfixed, items not linked to the umbrella
  vanish from active-work views; no per-thread focus view until G6 is fixed.

## Design Decisions

### Decision 1: Fix the single-focus baseline before generalizing
Options: build multi-focus first; fix the baseline first.
**Chosen: fix the baseline first.** G1-G7 would be inherited and amplified by
any multi-focus design, and G1 alone already causes the user-visible failure
that triggered this proposal.

### Decision 2: Decouple "active leaf" from focus
Use the focus-independent definition (`planning_tree.py:510`) everywhere;
keep `is_current_focus_related` as informational metadata and a grouping key,
not a gate.
**Chosen**, so ad-hoc and new-thread work is never hidden by a stale focus.

### Decision 3: One status semantics
A non-`active` current focus is "no active focus" in every consumer (core
state, dashboard, resolver, snapshots); in that state work-item views are
ungated, never widened-or-narrowed inconsistently.
**Chosen**: define the rule once and test it across core state and resolver.

### Decision 4: Make "no active focus" a supported state
Options: optional `current_focus.md` (loader/validator/snapshot accept absence);
documented placeholder convention (`status: paused`).
**Chosen: placeholder convention first** (no schema change, depends on
Decision 3); revisit optional-file only if the placeholder proves awkward.

### Decision 5: Add a read-only focus registry and focus views (covers N1)
Load `current_focus.md`, `focus/proposed/*.md` and `focus/archive/**/*.md` into
a read-only collection; `current_focus` remains the single designated current
focus. Add a focus list and work-items-by-`related_focus` to `lrh serve`.
**Chosen**: it is option (a) plus the visibility the single model lacks.

### Decision 6: Interim LCATS guidance is option (d)
Refresh `current_focus.md` as an umbrella over the active threads and link
workstreams and work items to it.

### Decision 7: Defer option (b) with explicit entry conditions
Revisit multi-active foci only if, after Decisions 1-6 land, a project still
needs concurrently active foci. Entry conditions: update
`precedence_semantics.md` (same change set, per its Consequences), define a
primary-wins tie-break, amend the singular-focus statements (`design.md:438`;
`humans.md:431,1189,1733,2058`), and extend `RuntimeInvocation.focus_id`
(`precedence.py:12`) to match any active focus.

### Decision 8: Disposition of the unused resolver
Keep it as a tested library, document that it is not yet consumed, and do not
extend it for multi-focus until a consumer exists. Wiring it in or deleting it
is a separate decision.

## Precedence-Semantics Check

Checked against `project/memory/decisions/precedence_semantics.md`:
- "Focus narrows roadmap" is not threatened: several foci that each refine the
  same roadmap still only narrow it.
- Invariants 1-3 and 5 hold under any option if foci are unioned; Invariant 4
  ("focus mismatch is a consistency issue") needs a rule for matching any of
  several active foci, since `RuntimeInvocation.focus_id` is a single string
  (`precedence.py:12,99`) and `ResolvedState.active_focus` is singular
  (`precedence.py:34`).
- The decision defines no tie-break between two foci at the same layer; option
  (b) must add one.
- The decision's Consequences require any precedence redesign to update the
  record, implementation and tests together; options (a) and (d) and
  Decisions 1-5 do not trigger that clause, option (b) does.
- Decision 3 aligns the live path with the record's existing statement that
  runtime state must not silently override loaded focus state.

## Non-Goals

- Does not implement anything; this is a design note.
- Does not change `precedence_semantics.md` or `design.md`; those edits follow
  adoption.
- Does not adopt multiple simultaneously active foci (option (b)).
- Does not decide whether the resolver is wired in or removed.
- Does not inspect or modify the LCATS repository.
- Does not address non-focus gaps in `lrh serve` or the desktop app.

## Implementation Plan

Medium-to-large scope: recommend a workstream (e.g. `WS-LRH-FOCUS-MODEL`) with
work items in this order:

1. Decouple active-leaf from focus (Decision 2); tests for G1.
2. Single focus-status semantics and placeholder convention (Decisions 3-4);
   cross-consumer tests for G2, G5.
3. Focus registry: validator glob, loader read-only collection (Decision 5, G7).
4. `lrh serve` focus list and work-items-by-focus views (Decision 5, G6).
5. Resolver disposition decision (Decision 8, G3).
6. Deferred: multi-active foci (Decision 7), only on demonstrated need.

## Cross-References

- Canonical design: `project/design/design.md` (precedence section; §15.1 focus schema)
- Human-facing model: `project/context/humans.md:417-437`
- Precedence decision: `project/memory/decisions/precedence_semantics.md`
- Adjacent proposal: `project/design/proposals/proposed/lrh-open-work/00_proposal.md`
