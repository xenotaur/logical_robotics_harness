---
id: "WI-LRH-CONSOLE-STATUSBOARD"
title: "Settle the statusboard band set and build the banded statusboard"
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
- "The owner's band-set decision is recorded in the visual-language proposal, and the statusboard matches it."
- "The statusboard renders every band, with icon, label, count, and description, in both themes, as the home view."
- "Every project appears in exactly one band, with its evidence chip and freshness; empty and Unknown states are explicit."
- "Bands collapse and expand without scripts."
- "Bands meet the token contrast targets, and no state is conveyed by color alone."
required_evidence:
- "test_output"
- "manual_review"
- "lrh_validate"
artifacts_expected:
- "src/lrh/serve.py"
- "src/lrh/ux/dashboard.py"
- "project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md"
- "tests/ (statusboard tests)"
---

# Banded statusboard

## Summary

Replace today's Meta page with the restrained, banded statusboard (Revision 2, Q2 and Q6). It starts by settling, with the owner, which band set to use, because Revision 2 and `PROP-META-OPERATIONAL-TRIAGE-SEMANTICS` disagree.

## Problem / Context

Revision 2 renames the Meta view's rows to bands and lists Needs attention, Blocked, Active work, Awaiting review, Stable, and Unknown. `PROP-META-OPERATIONAL-TRIAGE-SEMANTICS` instead targets Blocked, Needs Attention, Active Work, Ready for Work, No Action Needed, Archived, and Unknown, with Blocked first and Title Case labels (`project/design/proposals/proposed/meta-operational-triage-semantics/00_proposal.md:120`, `170-183`). The code already computes `triage_lane` per project (`src/lrh/ux/dashboard.py:227`, `src/lrh/serve.py:1222`). The visual reference is the restrained swimlane console in the Revision 2 mock.

### Duplication search

In-repo: the Meta page (`/meta` in `src/lrh/serve.py`) renders operational cards from `triage_lane`. Recommendation: proceed by restyling it, not by adding a new data model.

## Scope

- An owner decision on the band set, precedence, and label case, recorded in both proposals.
- The banded statusboard rendered from `triage_lane` values in the frame.
- Explicit empty and unknown states.

## Required Changes

1. Before building, present the two band sets to the owner and record the decision on the set, the order, and the label case in the visual-language proposal, with a cross-reference in the triage-semantics proposal. Decide whether to rename `triage_lane`; it is optional.
2. Render one band per state. Each band has a tinted header with icon, label, count, and short description, plus a left accent rail. Project cards show focus, next action, an evidence chip, and freshness.
3. Show empty bands explicitly, keep Unknown visible, and make bands collapsible without scripts.
4. Keep the `/meta` route as the statusboard URL, and make it the frame's home view.

## Non-Goals

- No new triage computation beyond the decided band mapping.
- No glow or neon styling; making it more striking is later work.

## Acceptance Criteria

- The owner's band-set decision is recorded in the visual-language proposal, and the statusboard matches it.
- The statusboard renders every band, with icon, label, count, and description, in both themes, as the home view.
- Every project appears in exactly one band, with its evidence chip and freshness; empty and Unknown states are explicit.
- Bands collapse and expand without scripts.
- Bands meet the token contrast targets, and no state is conveyed by color alone.

## Validation

- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- Check the statusboard by hand with the owner's Meta registry, in the app and in Chrome.

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-FRAME`.
- It can run before or after `WI-LRH-CONSOLE-MAP-STATIC`.

## Risk Notes

- Changing band membership changes what the owner sees as needing attention. Show the mapping from `triage_lane` values to bands in the PR, and test it.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md` (Revision 2 decisions)
- `project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md`
