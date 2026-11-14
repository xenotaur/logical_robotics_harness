---
id: "WI-LRH-FOCUS-ACTIVE-LEAF-DECOUPLE"
title: "Show active work in lrh serve and the dashboard regardless of its focus link"
type: "deliverable"
status: "proposed"
blocked: false
blocked_reason: null
resolution: null
owner: "anthony"
contributors:
- "anthony"
assigned_agents: []
parent_id: "WS-LRH-FOCUS-MODEL"
related_focus: []
related_roadmap: []
related_workstreams:
- "WS-LRH-FOCUS-MODEL"
related_design:
- "project/design/proposals/proposed/lrh-multi-focus-support/00_proposal.md"
depends_on: []
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
- "An active work item with no children and no related_focus appears in core state's active_leaf_work_items, in the serve payload's planning.active_leaves, and in the dashboard active-work count."
- "The serve payload's planning.active_leaf_ids and planning.active_leaves list the same work items."
- "An active work item that has children is still excluded from active leaves."
- "is_current_focus_related still reports whether a work item links to the current focus, and is no longer a condition of is_active_leaf."
required_evidence:
- "test_output"
- "lrh_validate"
artifacts_expected:
- "src/lrh/core_state.py"
- "tests/control_tests/core_state_test.py"
- "tests/ux_tests/dashboard_test.py"
- "tests/cli_tests/serve_test.py"
---

# Show active work in lrh serve and the dashboard regardless of its focus link

## Summary

"Active leaf" is defined twice. `WorkItemState.is_active_leaf` in core state
additionally requires the work item to link to the current focus, so active work
that is not linked to the current focus disappears from the `lrh serve` active
leaves list and the dashboard active-work count, with no diagnostic. Use one
definition, the focus-independent one, everywhere.

## Problem / Context

`src/lrh/control/planning_tree.py:510` marks a work item an active leaf when its
status is `active` and it has no children. `src/lrh/core_state.py:674-676`
additionally requires `is_current_focus_related`, computed at
`src/lrh/core_state.py:642-647` against the single loaded focus id. That
focus-gated flag feeds `active_leaf_work_items` (`core_state.py:410`), which
feeds:

- the serve payload's `planning.active_leaves` (`src/lrh/serve.py:866`) and the
  HTML active-leaves list (`serve.py:467`), and
- the dashboard card's active-work count (`src/lrh/ux/dashboard.py:386`).

The ungated planning-tree definition feeds `planning.active_leaf_ids`
(`serve.py:865`). The two fields in one payload can therefore disagree.

A downstream project (LCATS) hit this: its `current_focus.md` was stale for a
new thread of work, so new work items without a link to that focus never
appeared as active work. This is gap G1 in
`project/design/proposals/proposed/lrh-multi-focus-support/00_proposal.md`
(Decision 2).

### Prior Art Check

#### Duplication search
- In-repo: No existing implementation found. Related: the proposal above.
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed

#### Demand search
- Work items: None found.
- Proposals: `PROP-LRH-MULTI-FOCUS-SUPPORT` Decision 2 requests this.
- Backlog: No matching entries.
- Recommendation: No action

## Scope

Make `WorkItemState.is_active_leaf` focus-independent so every active-work
surface uses the same definition. Keep `is_current_focus_related` as
informational metadata.

## Required Changes

- `src/lrh/core_state.py`: remove `and is_current_focus_related` from the
  `is_active_leaf` computation (`core_state.py:674-676`) so it matches
  `planning_tree.py:510`. Leave the `is_current_focus_related` field and its
  computation (`core_state.py:642-647`) in place.
- Add or update tests proving the acceptance criteria in
  `tests/control_tests/core_state_test.py`, `tests/ux_tests/dashboard_test.py`
  and `tests/cli_tests/serve_test.py`. Include an unlinked active leaf, a linked
  active leaf, and an active item with children.

## Non-Goals

- Does not add a focus filter, focus grouping or focus list to `lrh serve`
  (proposal Decision 5).
- Does not change focus status semantics (`WI-LRH-FOCUS-STATUS-SEMANTICS`).
- Does not change `planning_tree.py`'s definition, which is already
  focus-independent.

## Acceptance Criteria

- An active work item with no children and no `related_focus` appears in core
  state's `active_leaf_work_items`, in the serve payload's
  `planning.active_leaves`, and in the dashboard active-work count.
- The serve payload's `planning.active_leaf_ids` and `planning.active_leaves`
  list the same work items.
- An active work item that has children is still excluded from active leaves.
- `is_current_focus_related` still reports whether a work item links to the
  current focus, and is no longer a condition of `is_active_leaf`.

## Validation

```bash
scripts/version tools
scripts/format --check --diff
scripts/lint
scripts/test
lrh validate
```

## Dependencies / Order

None. `WI-LRH-FOCUS-STATUS-SEMANTICS` depends on this work item because both
edit `src/lrh/core_state.py` near lines 642-676.

## Risk Notes

- The dashboard active-work count and the `lrh serve` active-leaves list may
  grow in projects whose focus link is stale, which is the intended effect.
  Check that any existing test asserting the old, smaller count is updated for
  the right reason rather than loosened.

## Related Workstream and Designs

- `project/workstreams/proposed/WS-LRH-FOCUS-MODEL.md`
- `project/design/proposals/proposed/lrh-multi-focus-support/00_proposal.md`
