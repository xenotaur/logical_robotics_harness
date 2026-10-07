---
id: "WI-LRH-CONSOLE-L1-DOGFOOD"
title: "Dogfood the L1 dependency map on real LRH and LCATS planning questions"
type: "operation"
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
depends_on:
- "WI-LRH-CONSOLE-MAP-STATIC"
blocked_by: []
expected_actions:
- "create_file"
- "edit_file"
- "run_tests"
- "create_report"
- "create_pr"
forbidden_actions:
- "force_push"
- "delete_branch"
- "merge_pr"
- "publish_package"
- "deploy_remote_service"
- "fabricate_dogfood_sessions"
- "implement_project_mutation"
- "run_lrh_agentic"
acceptance:
- "LCATS is served through the Meta registry; any gap found on the way is filed as a linked work item and resolved before this item resolves."
- "Three genuine planning questions spanning both LRH and LCATS, with at least one answered on the LCATS map, are answered with answers traceable to source records."
- "The adverse cases are exercised and recorded with real results, including render time on the largest real view."
- "`project/evidence/EV-LRH-CONSOLE-L1-DOGFOOD.md` follows the evidence schema, records its limitations, and recommends next steps for L2."
required_evidence:
- "manual_review"
- "lrh_validate"
- "validation_output"
- "test_output"
artifacts_expected:
- "project/evidence/EV-LRH-CONSOLE-L1-DOGFOOD.md"
- "project/views/dependency_maps/ (LRH view)"
- "LCATS project/views/dependency_maps/ (separate LCATS PR)"
---

# L1 dependency-map dogfood

## Summary

Run the L1 evidence gate: answer three genuine planning questions across LRH and LCATS on the dependency map, with answers traced to source records. Exercise the adverse cases, and record evidence and a recommendation for L2.

## Problem / Context

The dogfood proposal's L1 gate is 'Three LRH/LCATS planning questions answered with traceable evidence and adverse graph fixtures' (`project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md:307`). At L1 it asks to verify cycles, missing IDs, hidden dependencies, ambiguous lanes, absent phases, stale snapshots, and larger real project views, and says: 'Do not substitute the attractive synthetic example for the real-project pilot' (`project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md:286-289`). L0 dogfood used LRH only, so LCATS access through the Meta registry has not yet been exercised by the console.

### Duplication search

In-repo: `project/evidence/EV-LRH-CONSOLE-DESKTOP-L0-DOGFOOD.md` is the model for the evidence record. No L1 evidence exists. Recommendation: proceed.

## Scope

- Confirm that the console can serve an LCATS map through the Meta registry, or file a work item for the gap.
- Declare real views for LRH and LCATS.
- Answer three genuine planning questions with traceable answers.
- Run the adverse checks.
- Write an evidence record and an L2 recommendation.

## Required Changes

1. Check first whether the console can serve LCATS's workspace through the Meta registry (`src/lrh/meta/workspace.py`) and render its dependency map. If it cannot, file a work item in this repository for the gap (an LCATS-side change gets a tracking work item here), add its ID to `blocked_by`, and, with this item active, set `blocked: true` with a `blocked_reason` until the gap is resolved. LRH sessions may continue meanwhile, but the gate cannot pass on LRH alone.
2. Declare the LRH dependency-map view in this repository's `project/views/dependency_maps/`. The LCATS view lands as a separate LCATS PR, only with the owner's authorization; link it from the evidence.
3. With the owner, record three genuine planning questions, for example what can move now, why an item is waiting, or what unblocks the most work. Answer each from the map, with links to source records.
4. Exercise and record the adverse cases: cycles, missing IDs, hidden dependencies, ambiguous lanes, absent phases, stale snapshots, and the largest real view, with render times.
5. Write `project/evidence/EV-LRH-CONSOLE-L1-DOGFOOD.md`, including limitations and a recommendation for L2. Code defects become new work items.

## Non-Goals

- No app or backend code changes; record defects as work items.
- No synthetic or invented sessions or answers.

## Acceptance Criteria

- LCATS is served through the Meta registry; any gap found on the way is filed as a linked work item and resolved before this item resolves.
- Three genuine planning questions spanning both LRH and LCATS, with at least one answered on the LCATS map, are answered with answers traceable to source records.
- The adverse cases are exercised and recorded with real results, including render time on the largest real view.
- `project/evidence/EV-LRH-CONSOLE-L1-DOGFOOD.md` follows the evidence schema, records its limitations, and recommends next steps for L2.

## Validation

- `lrh validate`
- `scripts/test`
- The owner's sessions with the map, in the app and in Chrome.

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-MAP-STATIC`. `WI-LRH-CONSOLE-INTERACTIVE` may be used if it has landed, but is not required.

## Risk Notes

- Sessions must be the owner's real use. An agent may draft the evidence from the owner's notes, but must not invent sessions or answers.
- Without an LCATS view the gate is only half met. The item stays incomplete until the LCATS map answers at least one question; LRH alone never passes it.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md` (Revision 2 decisions)
- `project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md`
