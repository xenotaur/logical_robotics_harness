---
id: "WS-LRH-CONSOLE-LOCAL-DOGFOOD"
kind: "planning_node"
title: "LRH Console Local Dogfood"
status: "proposed"
stage: "planned"
origin: "design_review"
parent_id: null
children: []
summary: "Make Serve, Meta, and dependency planning useful from a local app through evidence-gated dogfood increments."
related_focus: []
related_roadmap: []
related_design:
- "project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md"
- "project/design/execution_framework_mvp.md"
work_items:
- "WI-LRH-CONSOLE-DESKTOP-PROTOCOL"
- "WI-LRH-CONSOLE-DESKTOP-L0"
execution_records: []
evidence: []
exit_criteria:
- "Local L0-L4 slices have reviewed implementation/evidence, or an explicit reviewed scope revision records deferral."
- "LRH and LCATS dependency planning works in app and Chrome with source-traceable blockers, uncertainty, and structural\
  \ parallelism."
- "Owned-process lifecycle, recovery, capability isolation, and CLI coexistence are validated on every claimed platform."
- "Daily multi-project use, local packaging, and bounded handoff meet their recorded evidence gates."
- "Closeout reconciles work-item state, workstream scope, and the next remote decision without treating planning\
  \ capture as runtime completion."
---

# LRH Console local dogfood

## Purpose

Make Serve, Meta, and dependency planning convenient in ordinary coding and
browser work. Coordinate the local desktop lifecycle, shared graph semantics,
daily workspace use, packaging, and bounded handoff as a sequence of useful
prototypes. The first meaningful product outcome is L0 + L1: open from the Dock,
select LRH or LCATS, and answer a real dependency question without starting a
terminal server.

This is a proposed planning node. `stage: planned` records that the approved
direction has a roadmap and two initial leaves; it does not activate execution or
reprioritize current focus. Later leaves are added when preceding dogfood gates
have produced evidence. It is a top-level console workstream related to the
existing execution framework, without changing that workstream's ownership.

## Scope

- L0: explicit Python server protocol and Tauri app with one default content
  window, native lifecycle menus, on-demand Settings/Details, and Chrome handoff.
- L1: typed shared dependency map, workstream/conceptual lanes, explicit phase
  rows, accessible interactions, and honest readiness/parallelism semantics.
- L2–L3: daily multi-project Meta navigation and self-contained desktop packaging,
  with Mac first and platform-specific Linux/Windows validation later.
- L4: reuse prompt/packet previews for bounded coding-app handoff and evidence
  return, preserving existing execution/approval authority.

## Prior Art Check

### Duplication search

- In-repo: reuse `src/lrh/serve.py`, `src/lrh/core_state.py`, typed control models,
  planning relationships, and the existing execution-framework workbench. No
  complete Tauri supervisor or dependency-map renderer found in tracked source
  and planning searches at `8603b6514329ea242294da420aa448d2fc959fd1`.
- Sibling repos: LCATS is a consumer candidate, not inspected for this capture.
- External libraries: adopt Tauri and evaluate maintained graph rendering/layout
  components at L1 rather than building platform infrastructure.
- Open PR context: PR #719 concerns local-agent experiments, not this console
  lifecycle/map slice; coordinate later handoff work without duplicating runtime.
- Recommendation: proceed with a console workstream extending the current backend.

### Demand search

- Work items: `WI-WORK-ITEM-BLOCKED-STATE-EXPRESSIVENESS` is relevant to honest graph
  blocker display, but its policy change is not part of these first leaves.
- Proposals: related visual language, Serve triage, Meta triage, and activity-lane
  proposals are linked in the companion design; none is superseded here.
- Backlog: inconsistent blocked-field propagation at `project/design/backlog.md:641`
  must be assessed when implementing the graph projection.
- Recommendation: preserve these as related demands. This planning package does
  not close existing requests or claim their implementation is complete.

## Work Items

1. **WI-LRH-CONSOLE-DESKTOP-PROTOCOL** — implement and document a versioned
   machine startup/shutdown contract around the existing service, including
   loopback port discovery, workspace identity, bounded lifecycle, and parent loss.
2. **WI-LRH-CONSOLE-DESKTOP-L0** — consume that contract from a Tauri shell with
   native menus, a default content window, one on-demand Settings/Details window,
   private configuration, browser handoff, and recorded macOS dogfood.
   Depends on the protocol work item.

Only these two leaves are created initially. L1's snapshot/view schema and
renderer, then L2–L4, will receive bounded items after the preceding evidence gates.
A partial L0 implementation cannot close this local dogfood workstream.

## Sequence and decision gates

| Increment | Required evidence before advancing |
| --- | --- |
| L0 | Protocol failure tests and five terminal-free macOS sessions, including close/reopen, crash recovery, Stop/Restart/Quit, and browser handoff. |
| L1 | Three real planning questions across LRH and LCATS, traced to source; same semantics in Chrome and app; adverse graph fixtures and keyboard/table path. |
| L2 | Daily use across several projects; stable workspace/project identity, explicit stale state, and actionable errors. |
| L3 | Self-contained Mac operation through reboot and sleep/wake without shell setup; Linux/Windows distribution validated when added. |
| L4 | Several real prompt/packet handoff → coding → evidence/review cycles without inventing execution or completion state. |

R1 private snapshots, R2 private live hosting, R3 invited read-only access, R4 remote
commands, and native mobile are later candidate workstreams. The design keeps
those boundaries open but their delivery is not an exit criterion here.

## Exit Criteria

- L0–L4 local slices have reviewed implementation and evidence records, or an
  explicit reviewed scope revision documents any deferred slice.
- LRH and LCATS dependency planning is demonstrated from app and Chrome with
  source-traceable blockers and structural parallelism, including uncertainty.
- Process ownership, recovery, navigation/capability isolation, and CLI coexistence
  are validated on each platform claimed as supported.
- Local packaging and daily multi-project use meet their recorded gates; handoff
  preserves current execution policy and evidence semantics.
- Work-item states, workstream scope, and the next remote decision are reconciled
  in closeout; this creation PR alone does not satisfy any runtime exit criterion.

## Non-Goals

- Do not deploy or expose a remote server, implement mobile distribution, or
  deliver remote collaboration under this local workstream.
- Do not rewrite Python domain logic, build a scheduler, infer dates from graph
  placement, or change canonical blocker policy as a display shortcut.
- Do not activate autonomous execution, project mutation, merge, or publishing.
- Do not make the default UI a permanent server-management window.

## Relationship to Design

The governing proposal candidate is
`project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md`.
Its repository evidence, alternatives, semantic rules, and remote sequence are the
review basis. Existing execution authority remains with
`project/design/execution_framework_mvp.md`; current focus is unchanged.

## Open Questions

The first implementation item fixes the exact protocol and timeout/version rules.
L1 fixes view schema and graph components after inspecting real consumer data.
Platform signing and remote identity decisions are deferred to their delivery
stages. IDs, owner convention, and initial planning stage were inferred from the
approved discussion and repository conventions for this review package.
