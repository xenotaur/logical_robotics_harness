---
id: "WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT"
title: "Add an indented outline layout that orders cards by dependency depth"
type: "deliverable"
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
- "create_pr"
forbidden_actions:
- "force_push"
- "delete_branch"
- "merge_pr"
- "publish_package"
- "deploy_remote_service"
acceptance:
- "An outline layout orders each lane's cards topologically and indents them by dependency depth, behind the existing `Layout` interface, with no renderer changes beyond choosing the layout."
- "Cycles and offscreen references are handled without errors, and diagnostics stay visible."
- "The owner has compared both layouts on a real view, and the default-layout decision is recorded."
required_evidence:
- "test_output"
- "manual_review"
- "lrh_validate"
artifacts_expected:
- "src/lrh/dependency_maps/layout.py"
- "src/lrh/serve.py"
- "tests/dependency_maps_tests/render_test.py"
- "project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md"
---

# Indented outline map layout

## Summary

Add a second dependency-map layout, behind the existing `Layout` interface, that orders each lane's cards topologically and indents each card by its dependency depth. This makes the lines easier to follow than in the default `layered-grid` layout. Make it the default once the owner has reviewed it.

## Problem / Context

While checking PR #800 (`WI-LRH-CONSOLE-MAP-STATIC`) in LRH Console, the owner reported that lines are 'somewhat hard to read'. They suggested 'ordering them vertically in a partial order and indenting cards at each deeper level'. The default `LayeredGridLayout` keeps cards in their fixed lane and phase cells, orders them with barycenter sweeps, and routes every line through the gutters, so a single-lane view becomes one tall column with many parallel lines. The visual-language proposal (Revision 2, Q7) already expects pluggable layouts.

### Duplication search

In-repo: `src/lrh/dependency_maps/layout.py` defines `Layout` and `LayeredGridLayout`, and nothing else orders cards by depth. Recommendation: proceed with a second `Layout` implementation.

## Scope

- A new `Layout` implementation, for example `OutlineLayout` (`outline`): within each lane, cards in a topological order of `depends_on` and `blocked_by`, each indented by its dependency depth.
- Phases stay organizational rows, and a cycle falls back to a stable order with a diagnostic.
- A way to choose the layout per page (for example `?layout=outline`), and a decision with the owner on which is the default.
- Lines routed for the indented positions, still right-angled, from prerequisite to dependent.

## Required Changes

1. Implement the outline layout in `src/lrh/dependency_maps/layout.py` behind the existing interface. Cover topological order, depth indentation, cycles, offscreen references, and multiple lanes, with tests on fixed fixtures.
2. Let the map page choose the layout through the URL, with the default unchanged until the owner decides.
3. Check this workstream's real view in LRH Console with the owner, then record the default-layout decision in the PR and in the visual-language proposal.

## Non-Goals

- No scripts; interaction is `WI-LRH-CONSOLE-INTERACTIVE`.
- No change to the snapshot.
- No curved router.

## Acceptance Criteria

- An outline layout orders each lane's cards topologically and indents them by dependency depth, behind the existing `Layout` interface, with no renderer changes beyond choosing the layout.
- Cycles and offscreen references are handled without errors, and diagnostics stay visible.
- The owner has compared both layouts on a real view, and the default-layout decision is recorded.

## Validation

- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- Compare both layouts on `lrh-console-l1` in LRH Console with the owner.

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-MAP-STATIC`.
- Independent of `WI-LRH-CONSOLE-INTERACTIVE`; the interactive mode consumes whichever layout is chosen.

## Risk Notes

- Deep chains could make cards very narrow; cap the indentation and say so in the layout's documentation.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md` (Revision 2 decisions)
- `project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md`
