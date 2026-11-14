---
id: "WS-LRH-FOCUS-MODEL"
kind: "planning_node"
title: "LRH Focus Model Baseline"
status: "proposed"
stage: "assessed"
origin: "design_review"
parent_id: null
children: []
summary: "Make the single-focus model coherent before generalizing it: decouple active-work views from focus and give focus status one meaning everywhere."
related_focus: []
related_roadmap: []
related_design:
- "project/design/proposals/proposed/lrh-multi-focus-support/00_proposal.md"
- "project/memory/decisions/precedence_semantics.md"
- "project/work_items/proposed/WI-LRH-PROJECT-UPDATE-SKILL.md"
work_items:
- "WI-LRH-FOCUS-ACTIVE-LEAF-DECOUPLE"
- "WI-LRH-FOCUS-STATUS-SEMANTICS"
exit_criteria:
- "An active leaf work item appears in core state's active_leaf_work_items, planning.active_leaves, and the dashboard active-work count whether or not it links to the current focus, and active_leaf_ids and active_leaves agree."
- "A non-active current focus resolves as no active focus identically in core state, the precedence resolver (including when a runtime focus_id matches it), and the focus-scoped snapshot, with a test for each."
- "precedence_semantics.md records the focus-status rule, updated in the same change as the resolver."
- "The no-active-focus state (a paused current_focus.md) is documented as supported."
- "Each deferred item (focus registry and lrh serve focus views, resolver disposition, multi-active foci) is either scheduled as a new work item or explicitly dropped, with the reason recorded in this workstream."
---

# LRH Focus Model Baseline

## Purpose

This workstream groups the first two baseline fixes recommended by
`PROP-LRH-MULTI-FOCUS-SUPPORT` (merged in PR #825). Both address defects,
verified against `main`, that make a stale or paused focus silently
under-report work: active work not linked to the current focus drops out of the
`lrh serve` and dashboard active-work views, and a paused focus means three
different things in three different consumers.

The proposal recommends fixing this single-focus baseline before considering
several simultaneously active foci, so this workstream covers only the
baseline. It exists now because a downstream project (LCATS) hit the symptom
directly: a stale `current_focus.md` hid new-thread work.

## Scope

- Decouple "active leaf" from focus (proposal Decision 2).
- Give a non-active current focus one meaning across core state, the
  precedence resolver and focus-scoped snapshots, and document the paused
  `current_focus.md` as the supported no-active-focus state (proposal
  Decisions 3 and 4).

## Prior Art Check

### Duplication search
- In-repo: No existing implementation found. Adjacent but distinct:
  `WI-LRH-CONSOLE-INVALID-PROJECT-STILL-LOADS` (a single invalid work item
  blanking a project) and `PROP-LRH-OPEN-WORK` (audits focus staleness without
  changing the model).
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed

### Demand search
- Work items: `WI-LRH-PROJECT-UPDATE-SKILL.md:112` names a planned owner
  design session on the focus construct as a related dependency; it does not
  request or satisfy this work.
- Proposals: `PROP-LRH-MULTI-FOCUS-SUPPORT` (Decisions 2-4) is the source of
  this work.
- Backlog: No matching entries.
- Recommendation: No action

## Work Items

Order matters: the second work item depends on the first, because both edit
`src/lrh/core_state.py` near lines 642-676.

1. `WI-LRH-FOCUS-ACTIVE-LEAF-DECOUPLE` — show active work in `lrh serve` and the
   dashboard regardless of its focus link.
2. `WI-LRH-FOCUS-STATUS-SEMANTICS` — give a non-active current focus one meaning
   in core state, the resolver and snapshots.

## Exit Criteria

See the `exit_criteria` frontmatter. The last criterion keeps the deferred
decisions below from being silently forgotten: closing this workstream requires
each one to be scheduled or explicitly dropped.

## Non-Goals

- Does not allow several simultaneously active foci (proposal option (b)).
- Does not add a focus registry or focus views to `lrh serve` (proposal
  Decision 5).
- Does not wire the precedence resolver into production code or remove it
  (proposal Decision 8).
- Does not make `current_focus.md` optional (proposal Decision 4 chose the
  placeholder convention first).
- Does not change the LCATS repository.

## Deferred

These proposal decisions are intentionally not work items yet. Adopting,
amending or rejecting the proposal is the owner's decision, and the planned
focus design session may change them.

- **Decision 5:** a read-only focus registry (`focus/proposed/`) and focus
  views in `lrh serve`.
- **Decision 7:** multiple active foci, behind the entry conditions stated in
  the proposal.
- **Decision 8:** whether the unused precedence resolver is wired in or
  removed.
