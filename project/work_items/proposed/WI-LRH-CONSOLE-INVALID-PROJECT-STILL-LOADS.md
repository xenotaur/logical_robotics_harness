---
id: "WI-LRH-CONSOLE-INVALID-PROJECT-STILL-LOADS"
title: "Keep a project browsable in LRH Console when one work item fails validation"
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
- "project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md"
depends_on:
- "WI-LRH-CONSOLE-RUN-PACKET-READINESS"
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
- "A project with one work item whose run-packet fields fail validation still lists its other work items in LRH Console, and their pages load."
- "The failing item and its validation errors are shown, for example as a page whose Run packet (validated) row reads Fails with the errors, instead of every page returning 404."
- "Pages still say clearly that the project has validation errors, and nothing that requires a valid project, such as run-packet generation, runs on invalid data."
required_evidence:
- "test_output"
- "manual_review"
- "lrh_validate"
artifacts_expected:
- "src/lrh/core_state.py"
- "src/lrh/serve.py"
- "tests/cli_tests/serve_test.py"
---

# Invalid project still loads

## Summary

When one work item has invalid data, LRH Console should still show the rest of the project, and show that item's errors, instead of going blank.

## Problem / Context

While implementing `WI-LRH-CONSOLE-RUN-PACKET-READINESS` (PR #855), the implementing session found the following. Any work item that declares run-packet fields which then fail validation makes `lrh validate` fail. `core_state.load_core_project_state` then returns an empty project (`_has_state_blocking_errors`), so every work-item page in LRH Console returns 404. The cold review reproduced this for ten kinds of failure, including a bad enum, a wrong type, a missing field and `execution_ready: false` with other fields. An empty `title` also passes `lrh validate` but makes the loader raise.

So one typo in one item hides the whole project. It also means the work-item page's "Run packet (validated): Fails" row cannot appear on any project today. The owner asked for this to be tracked.

### Duplication search

In-repo: `DEPENDENCY_MAP_VIEW_ISSUE_CODES` already exempts some issue codes from blocking state loading. Recommendation: proceed, extending that approach or quarantining the failing items.

## Scope

- Decide which validation errors block loading a project in LRH Console and which only mark the item. Errors confined to one work item's optional run-packet fields are the first candidates.
- Show the failing item's errors on its page and in the project's diagnostics.
- Keep the CLI's `lrh validate` result unchanged.

## Required Changes

1. Let core state load when the only errors are item-local and non-structural, recording them as diagnostics.
2. Show them on the item's page and on the project page.
3. Add tests for a project with one invalid run-packet declaration.
4. Check with the owner in LRH Console.

## Non-Goals

- No relaxing of `lrh validate` itself.
- No change to run-packet generation.

## Acceptance Criteria

- A project with one work item whose run-packet fields fail validation still lists its other work items in LRH Console, and their pages load.
- The failing item and its validation errors are shown, for example as a page whose Run packet (validated) row reads Fails with the errors, instead of every page returning 404.
- Pages still say clearly that the project has validation errors, and nothing that requires a valid project, such as run-packet generation, runs on invalid data.

## Validation

- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- The owner checks a project with one invalid item in LRH Console.

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-RUN-PACKET-READINESS`.

## Risk Notes

- Other views (the map, the Statusboard) read the same core state. Loading a partly invalid project changes what they can show, so check them too.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/executions/WI-LRH-CONSOLE-RUN-PACKET-READINESS/`
