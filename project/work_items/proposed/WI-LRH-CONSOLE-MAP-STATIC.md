---
id: "WI-LRH-CONSOLE-MAP-STATIC"
title: "Render the static dependency map, table, and blockers views with a pluggable layout"
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
- "WI-LRH-CONSOLE-FRAME"
- "WI-LRH-CONSOLE-MAP-SNAPSHOT"
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
- "A declared view renders as a server-side map in the frame, with the default layered, right-angled layout, readable in both themes and with no scripts."
- "The PR records the evaluation of established layout libraries, and the default layout uses the chosen one; no layout engine is written from scratch."
- "The layout is reached through a named interface that a second implementation could replace without changing the renderer."
- "`?item=<id>` highlights upstream and downstream and renders the drawer with the three state layers and the not-modeled effort slot."
- "The Table and Blockers views show the same snapshot, and every map state has a table row."
- "Lines and status cues meet the token contrast targets, and state is never conveyed by color alone."
required_evidence:
- "test_output"
- "manual_review"
- "lrh_validate"
artifacts_expected:
- "src/lrh/dependency_maps/ (layout)"
- "src/lrh/serve.py"
- "src/lrh/ux/"
- "tests/ (layout and rendering tests)"
---

# Static dependency map

## Summary

Render the L1 dependency map on the server with no scripts, from the typed snapshot, inside the app frame. Layout is pluggable, with layered ordering and right-angled routing as the default (Revision 2, Q7). Add the accessible table view, the blockers view, and the static detail drawer.

## Problem / Context

The owner decided that layered layout is the default and that layouts are pluggable. Revision 2 recommends a Python layout interface whose output the static SVG and the later interactive mode both use. In the default layout, the lane and phase grid fixes each card's cell, so only in-cell ordering and line routing vary. Revision 2 recommends line styles by relationship type *(recommended)*: solid for depends on and dashed for blocked by. Its dotted style for review gates has no L1 edge to draw, because the snapshot has only `depends_on` and `blocked_by` edges. The dogfood proposal requires a table alternative, keyboard access, visible focus, contrast, and a focused list mode on narrow screens (`project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md:279-284`). The Revision 2 mock shows the target look.

### Duplication search

In-repo: no map rendering exists. Recommendation: proceed.

## Scope

- A layout interface and the default layered, right-angled implementation.
- Server-rendered SVG map pages, plus the Table and Blockers views.
- Static selection through `?item=<id>`, with upstream and downstream highlighted on the server.
- Empty and diagnostic states.

## Required Changes

1. First evaluate established graph layout and rendering libraries for accessibility, packaging, maintenance, and size, and record the choice in the PR (`project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md:71-73`, `:407-408`). Do not build a graph layout engine from scratch.
2. Add a named, swappable layout interface: snapshot in, positioned cards and routed lines out. The default layered, right-angled layout wraps the chosen library behind it, with tests on fixed fixtures.
3. Render the map as server-side HTML and SVG in the frame. Lane headers and phase rows come from the view. Cards show the mono ID, the title, a status pill (icon, text, color), a "not prompt-ready" flag when relevant, and the why-waiting or why-blocked line. Include a legend.
4. Support static selection: with `?item=<id>`, highlight that card's upstream and downstream cards and lines (selected lines get emphasis by width), and render the drawer. The drawer shows the three state layers, placement, why, needs and needed-by, the repo-relative source path, and an "Effort: not modeled yet" slot.
5. Add the Table view, a real table whose IDs are ordinary links to `?item=<id>`, styled as buttons (script-free selection cannot use native buttons, and the CSP blocks forms), and the Blockers view, which lists every waiting or blocked item with the records it needs.
6. Show explicit states for no declared view, Unplaced items, diagnostics such as cycles and missing IDs, and stale snapshots. Provide a focused list mode on narrow screens.

## Non-Goals

- No scripts; interaction is `WI-LRH-CONSOLE-INTERACTIVE`.
- No curved router yet; it is the expected second layout.
- No editing of work items.

## Acceptance Criteria

- A declared view renders as a server-side map in the frame, with the default layered, right-angled layout, readable in both themes and with no scripts.
- The PR records the evaluation of established layout libraries, and the default layout uses the chosen one; no layout engine is written from scratch.
- The layout is reached through a named interface that a second implementation could replace without changing the renderer.
- `?item=<id>` highlights upstream and downstream and renders the drawer with the three state layers and the not-modeled effort slot.
- The Table and Blockers views show the same snapshot, and every map state has a table row.
- Lines and status cues meet the token contrast targets, and state is never conveyed by color alone.

## Validation

- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- Check this repository's own view by hand in the app and in Chrome.

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-FRAME` and `WI-LRH-CONSOLE-MAP-SNAPSHOT`.
- `WI-LRH-CONSOLE-INTERACTIVE` and `WI-LRH-CONSOLE-L1-DOGFOOD` depend on it.

## Risk Notes

- Wide views can overflow. Use a horizontally scrolling map container, never page-level horizontal scrolling, and a list mode on narrow screens.
- Server-side routing of many lines can be slow. Measure render time on the largest real view; the dogfood sessions found Meta slow (R9).

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md` (Revision 2 decisions)
- `project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md`
