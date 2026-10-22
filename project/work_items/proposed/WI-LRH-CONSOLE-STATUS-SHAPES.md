---
id: "WI-LRH-CONSOLE-STATUS-SHAPES"
title: "Distinguish similar status hues by shape for color-vision safety"
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
- "In progress and Unblocked differ by fill (filled versus outlined), and Abandoned and Unknown differ by card fill and title treatment, and no new border style resembles Blocked's dashed border, in both themes."
- "Contrast tests still pass, and every state carries text, an icon and a shape cue."
- "The owner confirms the pairs are distinguishable, and the visual-language proposal records the rule."
required_evidence:
- "test_output"
- "manual_review"
- "lrh_validate"
artifacts_expected:
- "src/lrh/dependency_maps/render.py"
- "src/lrh/serve.py"
- "tests/dependency_maps_tests/render_test.py"
- "project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md"
---

# Status shapes for similar hues

## Summary

Make the two pairs of similar-looking structural states distinguishable by shape, not only by hue. The pairs are In progress and Unblocked (both blue) and Abandoned and Unknown (both gray). Record the change in the visual-language proposal.

## Problem / Context

While checking PR #800 in LRH Console, the owner, who is partially red-green colorblind, reported that status hues are 'reasonably easy to tell apart' but that 'abandoned and unknown are similar and in progress and unblocked are similar'. Revision 2 (Q12) maps In progress to blue and Unblocked to sky blue, while Abandoned reuses the Unknown neutral. Every pill already carries an icon and text, so this item adds a stronger shape cue.

### Duplication search

In-repo: the status pills and cards are in `src/lrh/dependency_maps/render.py`, and the tokens are in `src/lrh/ux/static/lrh-tokens.css`. Recommendation: proceed.

## Scope

- Unblocked pills become outlined (hollow), and In progress pills stay filled.
- Abandoned cards get a muted (sunken) fill and a struck-through title, with their own icon. Unknown stays as it is, with its icon. Avoid a dotted border: it would be too close to the dashed border Blocked cards already use.
- The style specimen and the legend show the new shapes.
- The visual-language proposal's color-vision section records the change.

## Required Changes

1. Update the pill and card styles in `render.py` (and the specimen in `serve.py`) using tokens only, keeping contrast at the tested ratios.
2. Update the legend and specimen, and add tests that every state stays distinguishable without color, by text, icon and shape.
3. Record the shape rule in `project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md` under Color vision (Q12).
4. Check with the owner in LRH Console in light and dark mode.

## Non-Goals

- No new hues; the Okabe–Ito-derived palette stays.
- No change to state semantics.

## Acceptance Criteria

- In progress and Unblocked differ by fill (filled versus outlined), and Abandoned and Unknown differ by card fill and title treatment, and no new border style resembles Blocked's dashed border, in both themes.
- Contrast tests still pass, and every state carries text, an icon and a shape cue.
- The owner confirms the pairs are distinguishable, and the visual-language proposal records the rule.

## Validation

- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- The owner checks the map and specimen in LRH Console in light and dark mode.

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-MAP-STATIC`.
- `WI-LRH-CONSOLE-STATUSBOARD` should reuse the same pill shapes.

## Risk Notes

- An outlined pill with a light fill can lose contrast on sunken surfaces; check the text and border pairs against every surface.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md` (Revision 2 decisions)
- `project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md`
