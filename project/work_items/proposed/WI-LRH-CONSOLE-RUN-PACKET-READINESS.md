---
id: "WI-LRH-CONSOLE-RUN-PACKET-READINESS"
title: "Show the validated run-packet result on the work-item page and fix its blocked handling"
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
depends_on:
- "WI-LRH-CONSOLE-READINESS-VOCABULARY"
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
- "The work-item page shows whether the item passes the same run-packet validation that run-packet generation uses, with its errors when it does not, alongside the execution-ready flag."
- "The page's blocked handling uses the work item's `blocked` flag, not a `blocked` status that work items cannot have, and its wording never reports a set flag as No."
- "The Copy generated prompt button is enabled exactly when run-packet generation would succeed for the item, and the change to its gating is stated in the PR."
required_evidence:
- "test_output"
- "manual_review"
- "lrh_validate"
artifacts_expected:
- "src/lrh/serve.py"
- "tests/cli_tests/serve_test.py"
- "project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md"
---

# Validated run-packet readiness on the work-item page

## Summary

Show on LRH Console's work-item page whether a work item would actually pass run-packet generation, not only its `execution_ready` flag. Fix the page's blocked handling while doing so.

## Problem / Context

`WI-LRH-CONSOLE-READINESS-VOCABULARY` (PR #840) named each readiness check on the work-item page. Review found that "Execution-ready" read only the raw `execution_ready` frontmatter flag. Run-packet generation, `render_run_packet_from_work_item` in `src/lrh/assist/run_packet.py`, also runs `_validate_required_work_item_fields` and `validate_frontmatter(..., require_ready=True)` from `src/lrh/control/execution_readiness.py`. An item with only `execution_ready: true` therefore shows "Yes" and enables the Copy button, although generation rejects it. The owner chose to rename the label to "Execution-ready flag" in that PR, which changed labels only, and to file this item for the validated result.

The same review found an older defect. `render_project_work_item_page` (`src/lrh/serve.py`) treats `item.status == "blocked"` as blocked, both in its display ("No (the work item is blocked)") and in the Copy button's gating. Work items cannot have that status (`WORK_ITEM_STATUS` in `src/lrh/control/validator.py` is proposed, active, resolved and abandoned), so the check never fires. The real flag, `item.blocked`, is ignored. If the check were fixed as written, an item with its flag set would read "Execution-ready flag: No".

### Duplication search

In-repo: no existing item covers run-packet validation on the page. The workbench's run-packet preview route already renders the generation result. Recommendation: proceed, reusing the same validation.

## Scope

- On the work-item page, a run-packet result row: passes, or fails with the validation errors. Show it only for items that declare run-packet fields; others stay "Not declared".
- Blocked handling based on `item.blocked`, worded separately from the flag.
- Copy-button gating aligned with the validated result, recorded as a deliberate gating change.

## Required Changes

1. Compute the run-packet validation for the page's item with the same functions run-packet generation uses, without generating a packet.
2. Add the result row, and correct the blocked wording and check.
3. Gate the Copy button on the validated result, and state the change in the PR.
4. Add Serve tests for passing, failing, undeclared and blocked items. Update the vocabulary table in the visual-language proposal.
5. Check with the owner in LRH Console.

## Non-Goals

- No change to run-packet generation itself.
- No backfill of run-packet fields across work items.
- No change to the Statusboard counts. Whether they should count validated, flagged or prompt-ready items is the open triage question recorded in the visual-language proposal.

## Acceptance Criteria

- The work-item page shows whether the item passes the same run-packet validation that run-packet generation uses, with its errors when it does not, alongside the execution-ready flag.
- The page's blocked handling uses the work item's `blocked` flag, not a `blocked` status that work items cannot have, and its wording never reports a set flag as No.
- The Copy generated prompt button is enabled exactly when run-packet generation would succeed for the item, and the change to its gating is stated in the PR.

## Validation

- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- Owner check of a work item page in LRH Console.

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-READINESS-VOCABULARY` (resolved).

## Risk Notes

- This changes when the Copy button is enabled. No LRH work item declares run-packet fields today, so the visible effect on LRH is nil, but other projects may differ.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md` (readiness vocabulary)
- `project/executions/WI-LRH-CONSOLE-READINESS-VOCABULARY/`
