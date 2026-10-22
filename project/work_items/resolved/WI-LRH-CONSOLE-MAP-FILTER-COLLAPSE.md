---
id: "WI-LRH-CONSOLE-MAP-FILTER-COLLAPSE"
title: "Collapse the space left by filtered cards on the dependency map"
type: "deliverable"
status: "resolved"
blocked: false
blocked_reason: null
resolution: 'Implemented and merged in PR #835 (commit 4d4efd87). Dependency-map filters are now server-side: ?hide=<state>,... drops hidden cards before layout, so lanes and phases the filter empties disappear and lines re-route (LCATS worldcon-2026 with Done hidden: 50 cards in 5 lanes, 1948x3618 px, became 11 cards in 4 lanes, 1596x932 px). The selection and any unfinished item a shown item needs stay visible. The table and narrow-screen list follow the same filter, including items from outside the view, and the note counts them separately. The Show toggles are plain links that work without scripts, every in-page link keeps the filter, and a note counts what is hidden with Show all. Cards whose upstream is hidden say +N upstream hidden by filters, and the drawer gives hidden counts. Interactive tracing reads the full edge list, so it crosses hidden items. The owner checked it in LRH Console on LCATS and LRH, and re-checked after two changes made from that check. With scripts off, the page does not scroll to the selection.'
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
- "WI-LRH-CONSOLE-INTERACTIVE"
blocked_by: []
expected_actions:
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
- "Hiding a status filter (for example Done) re-lays out the map so hidden cards leave no empty rows or columns, and lines are re-routed for the remaining cards."
- "The no-script path agrees: a query parameter produces the same collapsed map server-side."
- "Filters still never hide an unfinished item that a shown item needs, and the user stays oriented (for example the selected card stays in view)."
- "The owner has checked the LCATS worldcon-2026 view with Done hidden in LRH Console."
required_evidence:
- "test_output"
- "manual_review"
- "lrh_validate"
artifacts_expected:
- "src/lrh/dependency_maps/render.py"
- "src/lrh/dependency_maps/layout.py"
- "src/lrh/serve.py"
- "tests/dependency_maps_tests/render_test.py"
- "tests/cli_tests/serve_test.py"
---

# Collapse filtered cards on the dependency map

## Summary

When a filter hides cards, lay the map out again without them, so the remaining cards fill the space.

## Problem / Context

`WI-LRH-CONSOLE-INTERACTIVE` hides filtered cards and lines with `visibility: hidden` (`src/lrh/dependency_maps/render.py`, around line 868), so the grid does not jump. The backlog entry "LRH Console UX feedback from the first interactive dogfood (layout redesign input)" already asked the redesign to revisit this. In the L1 dogfood (`project/evidence/EV-LRH-CONSOLE-L1-DOGFOOD.md`) the owner hit it in three of four runs: "makes the map be mostly wasted space if most items are hidden" (Run One), "most of the diagram is white space" (Run Two), and "Still hard to see all the cards with all that whitespace for suppressed items, even in a big window" (Run Four). On the LCATS worldcon-2026 view, 39 of the 50 in-view cards are done, so hiding Done leaves 11 cards spread across the full map. This item separates collapse from the wider layout redesign because it limited most sessions on its own.

### Duplication search

In-repo: `WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT` adds a second layout but does not re-lay out on filtering. Recommendation: proceed, and make collapse work with whichever layout is chosen.

## Scope

- Re-run the layout over the visible cards when a filter changes, in the client and server-side through a query parameter.
- Keep needed unfinished prerequisites visible, as filters do today.
- Keep the selected card, if any, in view after a collapse.

## Required Changes

1. Add a filter-aware layout pass (server-side query parameter first, so the no-script path works).
2. Make the interactive filters request or compute the collapsed layout.
3. Add tests for collapsed layouts and kept prerequisites (`tests/dependency_maps_tests/render_test.py`), and a Serve test that the query parameter is parsed and returns the collapsed server-rendered page (`tests/cli_tests/serve_test.py`).
4. Check with the owner on the LCATS and LRH views.

## Non-Goals

- No new layout algorithm; that is `WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT`.
- No change to the snapshot.

## Acceptance Criteria

- Hiding a status filter (for example Done) re-lays out the map so hidden cards leave no empty rows or columns, and lines are re-routed for the remaining cards.
- The no-script path agrees: a query parameter produces the same collapsed map server-side.
- Filters still never hide an unfinished item that a shown item needs, and the user stays oriented (for example the selected card stays in view).
- The owner has checked the LCATS worldcon-2026 view with Done hidden in LRH Console.

## Validation

- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- Owner check in LRH Console on `worldcon-2026` (LCATS) and `lrh-console-l1` (LRH).

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-INTERACTIVE` (resolved).
- Coordinate with `WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT`; either may land first. Recommended before L2.

## Risk Notes

- Re-layout moves cards, which the original design avoided to keep users oriented; keep the selected card anchored.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/evidence/EV-LRH-CONSOLE-L1-DOGFOOD.md`
- `project/design/backlog.md` (LRH Console UX feedback, layout redesign input)
