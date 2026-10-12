---
id: "WI-LRH-CONSOLE-MAP-PLANNING-CONTEXT"
title: "Design how the map shows workstream and proposal context, and project-wide outstanding work"
type: "investigation"
status: "proposed"
blocked: false
blocked_reason: null
resolution: null
owner: "anthony"
contributors:
- "anthony"
assigned_agents: []
parent_id: "WS-LRH-CONSOLE-LOCAL-DOGFOOD"
related_focus: []
related_roadmap: []
related_workstreams:
- "WS-LRH-CONSOLE-LOCAL-DOGFOOD"
related_design:
- "project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md"
- "project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md"
depends_on: []
blocked_by: []
expected_actions:
- "create_file"
- "edit_file"
- "create_pr"
forbidden_actions:
- "force_push"
- "delete_branch"
- "merge_pr"
- "publish_package"
- "deploy_remote_service"
acceptance:
- "A design, agreed with the owner, says how a lane shows its workstream's status, stage, and open questions, and how linked design proposals appear."
- "The design says how LRH Console answers 'what is outstanding across this project', given that a declared view covers only the workstreams it names."
- "The design names the implementation work items that follow, filed in this workstream or the L2 plan."
required_evidence:
- "manual_review"
- "lrh_validate"
artifacts_expected:
- "project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md"
---

# Planning context on the dependency map

## Summary

Design how the dependency map shows the planning records around work items (workstreams and design proposals), and how the console answers project-wide "what's outstanding" questions. This is the main design question the L1 dogfood raised for L2.

## Problem / Context

In the L1 dogfood (`project/evidence/EV-LRH-CONSOLE-L1-DOGFOOD.md`):

- **Run One (LCATS):** asked what work remains on special-character cleanup, the owner found no open work items but was "not confident here", because "the workstream and design proposal aren't in the dependency map and have no status listed". The records confirm the gap: all 10 work items in `WS-SPECIALS-CLEANUP` are resolved, but the workstream is still `proposed` with two open questions, which the map cannot show.
- **Run Two (LRH):** asked what work is outstanding in LRH, the owner found four open cards on the only LRH view, `lrh-console-l1`. That view covers 1 of LRH's 12 open workstreams (4 active, 8 proposed) and none of its 19 proposed design proposals.
- **Run Four (LRH):** the owner noted that the four open cards "do not well reflect the ~10 open threads on the console".

### Duplication search

In-repo: views are declared per file in `project/views/dependency_maps/`, and lanes are workstreams. Nothing renders workstream status or proposals on the map, and no project-wide view exists. `/lrh-work-remains` reports remaining work in a session, not in the console. Recommendation: proceed with a design.

## Scope

- Lane headers or a side panel with workstream status, stage, open questions, and linked proposals.
- A project-wide entry point: for example a generated view of all open workstreams, or a statusboard drill-down.
- Whether views should pick up work items added to their workstreams later (Run Two found them in an Unplaced row).

## Required Changes

1. Draft the design with the owner, as a revision of the visual-language proposal or a new proposal.
2. File the follow-up implementation work items.

## Non-Goals

- No implementation in this item.
- No agent dispatch; the per-lane "work remains" button idea is in the backlog.

## Acceptance Criteria

- A design, agreed with the owner, says how a lane shows its workstream's status, stage, and open questions, and how linked design proposals appear.
- The design says how LRH Console answers 'what is outstanding across this project', given that a declared view covers only the workstreams it names.
- The design names the implementation work items that follow, filed in this workstream or the L2 plan.

## Validation

- `lrh validate`
- Owner review of the design.

## Dependencies / Order

- None. Treat as the main L2 design question.

## Risk Notes

- A project-wide map of LRH's 55 open work items may be too large for the grid layout; consider it together with `WI-LRH-CONSOLE-MAP-FILTER-COLLAPSE` and `WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT`.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/evidence/EV-LRH-CONSOLE-L1-DOGFOOD.md`
- `project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md`
