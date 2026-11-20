---
id: "WI-LRH-FOCUS-STATUS-SEMANTICS"
title: "Give a non-active current focus one meaning in core state, the resolver and snapshots"
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
- "project/memory/decisions/precedence_semantics.md"
depends_on:
- "WI-LRH-FOCUS-ACTIVE-LEAF-DECOUPLE"
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
- "A current focus whose status is not active (for example paused) yields no active focus in core state, the precedence resolver, and the focus-scoped snapshot, through one shared rule."
- "The precedence resolver returns no active focus for a non-active focus in all three runtime cases: no runtime focus_id, a mismatching focus_id, and a matching focus_id. Each case has a test."
- "lrh snapshot current_focus with a non-active current focus includes all work items and states in its filtering note that there is no active focus, instead of filtering by that focus's id."
- "project/memory/decisions/precedence_semantics.md states the focus-status rule and the matching-runtime-id behavior, updated in the same change as the resolver and its tests."
- "A paused current_focus.md is documented as the supported no-active-focus state in project/design/design.md section 15.1 and docs/explanations/precedence-model.md."
required_evidence:
- "test_output"
- "lrh_validate"
- "manual_review"
artifacts_expected:
- "src/lrh/core_state.py"
- "src/lrh/control_plane/precedence.py"
- "src/lrh/assist/snapshot_cli.py"
- "tests/control_plane_tests/precedence_test.py"
- "tests/control_tests/core_state_test.py"
- "tests/assist_tests/snapshot_cli_test.py"
- "project/memory/decisions/precedence_semantics.md"
- "project/design/design.md"
- "docs/explanations/precedence-model.md"
---

# Give a non-active current focus one meaning in core state, the resolver and snapshots

## Summary

A paused (or otherwise non-active) current focus behaves three different ways
depending on which code reads it. Define one rule, "a non-active current focus
is no active focus", apply it in every consumer, record it in
`precedence_semantics.md`, and document the paused `current_focus.md` as the
supported way to say "no active focus right now".

## Problem / Context

`FOCUS_STATUS` allows six values (`src/lrh/control/validator.py:26`) and nothing
requires `current_focus.md` to be `active`. A non-active current focus then
means:

1. `src/lrh/core_state.py:642` ignores status entirely: a paused focus still
   reports as the current focus.
2. With no runtime `focus_id`, or a mismatching one, the resolver treats it as
   no focus (`src/lrh/control_plane/precedence.py:89,105`), and with no focus
   `precedence.py:117` puts every work item in scope.
3. With a matching runtime `focus_id`, `precedence.py:107` returns the loaded
   focus regardless of status, so a paused focus resolves as active.

The focus-scoped snapshot filters by the paused focus's id
(`src/lrh/assist/snapshot_cli.py:607-632`). This is gap G2 in
`project/design/proposals/proposed/lrh-multi-focus-support/00_proposal.md`
(Decisions 3 and 4); the third behavior was found by review of that proposal.

Because this changes canonical resolver behavior, the change-control clause in
`project/memory/decisions/precedence_semantics.md` applies: the record, the
implementation and the tests must change in the same change set.

### Prior Art Check

#### Duplication search
- In-repo: No existing implementation found. Adjacent:
  `WI-LRH-CONSOLE-INVALID-PROJECT-STILL-LOADS` (a different blanking cause).
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed

#### Demand search
- Work items: None found.
- Proposals: `PROP-LRH-MULTI-FOCUS-SUPPORT` Decisions 3 and 4 request this.
- Backlog: No matching entries.
- Recommendation: No action

## Scope

One shared definition of "active focus", applied in core state, the resolver and
the focus-scoped snapshot, with the decision record and docs updated in the same
change.

## Required Changes

- Add one shared rule (for example a small helper) that decides whether a
  loaded focus is active, and use it in `src/lrh/core_state.py`,
  `src/lrh/control_plane/precedence.py` and `src/lrh/assist/snapshot_cli.py`
  instead of each reading `status` on its own.
- `precedence.py`: make the matching-runtime-id branch (`precedence.py:107`)
  return no focus for a non-active focus, consistent with `precedence.py:89,105`.
- `core_state.py`: for a non-active current focus, report
  `is_current_focus_related` as false, because the focus is not the active one.
  Keep the focus itself visible, with its status, in the payload.
- `snapshot_cli.py`: for a non-active current focus, include all work items and
  say in the filtering note that there is no active focus.
- Update `project/memory/decisions/precedence_semantics.md` with the status rule
  and the matching-runtime-id behavior, and add the tests, in the same change.
- Document the paused `current_focus.md` as the supported no-active-focus state
  in `project/design/design.md` section 15.1 and
  `docs/explanations/precedence-model.md`.

## Non-Goals

- Does not make `current_focus.md` optional or change the validator's
  `FILE_NOT_FOUND` handling (proposal Decision 4 chose the placeholder
  convention first).
- Does not wire `resolve_precedence` into production code or remove it
  (proposal Decision 8).
- Does not add a focus registry or focus views to `lrh serve`.

## Acceptance Criteria

- A current focus whose status is not `active` (for example `paused`) yields no
  active focus in core state, the precedence resolver and the focus-scoped
  snapshot, through one shared rule.
- The precedence resolver returns no active focus for a non-active focus in all
  three runtime cases: no runtime `focus_id`, a mismatching `focus_id`, and a
  matching `focus_id`. Each case has a test.
- `lrh snapshot current_focus` with a non-active current focus includes all work
  items and states in its filtering note that there is no active focus, instead
  of filtering by that focus's id.
- `project/memory/decisions/precedence_semantics.md` states the focus-status rule
  and the matching-runtime-id behavior, updated in the same change as the
  resolver and its tests.
- A paused `current_focus.md` is documented as the supported no-active-focus
  state in `project/design/design.md` section 15.1 and
  `docs/explanations/precedence-model.md`.

## Validation

```bash
scripts/version tools
scripts/format --check --diff
scripts/lint
scripts/test
lrh validate
```

## Dependencies / Order

Depends on `WI-LRH-FOCUS-ACTIVE-LEAF-DECOUPLE`: both edit
`src/lrh/core_state.py` near lines 642-676, and the decoupling removes the
focus gate from `is_active_leaf` first.

## Risk Notes

- The precedence-semantics record is a governing document. Keep its wording to
  what the code now does, and update its Consequences-required artifacts (the
  record, the implementation and the tests) together in one commit range.
- Existing tests may assert the old matching-id behavior for a non-active focus.
  Update them because the rule changed, and say so in the PR.

## Related Workstream and Designs

- `project/workstreams/proposed/WS-LRH-FOCUS-MODEL.md`
- `project/design/proposals/proposed/lrh-multi-focus-support/00_proposal.md`
- `project/memory/decisions/precedence_semantics.md`
