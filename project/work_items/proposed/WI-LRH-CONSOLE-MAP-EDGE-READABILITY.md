---
id: "WI-LRH-CONSOLE-MAP-EDGE-READABILITY"
title: "Design how dependency-map lines are drawn so connections can be followed"
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
depends_on:
- "WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT"
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
- "A line-drawing design, agreed with the owner in a design discussion, covers connection points, line style (including whether to revisit curved lines), how incoming and outgoing lines are told apart, and how hover or selection isolates a card's connections."
- "The design is recorded in the visual-language proposal, with the reasons for each choice and the options considered."
- "The implementation work items that follow are filed in this workstream."
required_evidence:
- "manual_review"
- "lrh_validate"
artifacts_expected:
- "project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md"
---

# Readable dependency-map lines

## Summary

Decide with the owner how LRH Console draws dependency lines so that a reader can follow what connects to what, in both the outline and grid layouts.

## Problem / Context

While comparing the outline and grid layouts for `WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT` (PR #842), the owner preferred the outline but found both hard to read. Their observations:

- "the in lines and out lines for some boxes seem to overlap, making it hard to know what's connected to what. But then in outline view some boxes have inputs on the left and right."
- "We may want to revisit the right-angle language or have separate input and output ports or a more organized set of arrows or perhaps color to distinguish them."
- "there are so many rectilinear lines that cross each other it's hard to tell what's going on. This is why we had curved lines in the prototype I think."
- "Sometimes you can follow the lines, sometimes not ... Even hovering doesn't seem to help."

The causes, from the code (`src/lrh/dependency_maps/layout.py`):

- In the outline, a prerequisite in the same cell enters a card from the left rail. Prerequisites in other lanes or phases enter through the grid's routes, which can end on either side of the card.
- Lines inside a cell share one rail, with tracks only 4 px apart.
- Highlighting bolds the related lines (`src/lrh/ux/static/lrh-interactive.js`) but does not dim the rest.

The visual-language proposal (Revision 2) chose right-angled lines over the prototype's curves. The owner noted that this was decided together and should be discussed again rather than reversed by default: "it's a whole conversation".

### Duplication search

In-repo: `WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT` explicitly excludes a curved router, and the backlog's layout-redesign entry mentions tangled lines without a design. Recommendation: proceed with a design discussion.

## Scope

- **Connection points:** for example, inputs always on one side and outputs on the other, or ports per edge kind.
- **Line style:** right-angled versus curved; spacing or bundling of parallel lines.
- **Telling lines apart:** incoming versus outgoing, by direction cues, color (CVD-safe: never red versus green alone), or both.
- **Isolating connections:** whether hover or selection dims unrelated lines and cards.
- **Both layouts:** whether each choice applies to the grid as well as the outline.

## Required Changes

1. Hold a design discussion with the owner. Bring options with sketches or screenshots, including the prototype's curves.
2. Record the decisions and their reasons in the visual-language proposal.
3. File the implementation work items.

## Non-Goals

- No implementation in this item.
- No change to the layouts' card ordering.

## Acceptance Criteria

- A line-drawing design, agreed with the owner in a design discussion, covers connection points, line style (including whether to revisit curved lines), how incoming and outgoing lines are told apart, and how hover or selection isolates a card's connections.
- The design is recorded in the visual-language proposal, with the reasons for each choice and the options considered.
- The implementation work items that follow are filed in this workstream.

## Validation

- `lrh validate`
- Owner review of the design.

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT`.

## Risk Notes

- Line changes interact with layout and with the colors and shapes in `WI-LRH-CONSOLE-STATUS-SHAPES`; keep every cue colorblind-safe.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md`
