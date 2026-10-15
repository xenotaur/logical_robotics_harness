---
id: "WI-LRH-CONSOLE-RESTART-REQUEST-TOKEN"
title: "Tie the restart confirmation guard to its own restart request"
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
- "WI-LRH-CONSOLE-DESKTOP-RESTART-SHORTCUT"
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
- "A confirmed shortcut restart releases the confirmation guard only when the worker claims that same restart, not a restart from Settings queued before or alongside it."
- "While a confirmed restart is still queued, no new confirmation can open, even if another restart has just finished and re-enabled the menu item."
- "A unit test covers a Settings restart racing a confirmed shortcut restart."
required_evidence:
- "test_output"
- "lrh_validate"
artifacts_expected:
- "apps/desktop/src-tauri/src/shell.rs"
---

# Restart request token

## Summary

Make the restart confirmation's guard release only when the worker claims the very restart the user confirmed.

## Problem / Context

`WI-LRH-CONSOLE-DESKTOP-RESTART-SHORTCUT` (PR #845) added `RestartGuard` in `apps/desktop/src-tauri/src/shell.rs`, with three states: idle, asking and confirmed. A confirmed shortcut restart holds the guard until the worker claims a restart. The confirm-fixes review found a narrow gap. `claimed()` cannot tell which queued restart it is taking: Settings' **Restart server now** sends the same `Action::Restart`. If a Settings restart is queued just before or alongside a confirmed shortcut restart, the worker releases the guard when it claims the Settings one. When that restart finishes, the menu item can re-enable while the confirmed restart is still queued, and a press in that sub-poll window could open a new prompt and queue a third restart. The owner asked for this to be tracked.

### Duplication search

In-repo: only `RestartGuard` handles this. Recommendation: proceed.

## Scope

- Distinguish the confirmed restart from other restarts in the action queue, for example with a request token or a counter, so the worker releases the guard only for it.

## Required Changes

1. Carry an identifier, or a separate action variant, for the confirmed restart from the dialog callback to the worker.
2. Release the guard only when that request is claimed or dropped.
3. Add a unit test for the race.

## Non-Goals

- No change to the shortcut, the menu item, or the dialog.

## Acceptance Criteria

- A confirmed shortcut restart releases the confirmation guard only when the worker claims that same restart, not a restart from Settings queued before or alongside it.
- While a confirmed restart is still queued, no new confirmation can open, even if another restart has just finished and re-enabled the menu item.
- A unit test covers a Settings restart racing a confirmed shortcut restart.

## Validation

- `scripts/format --check --diff --desktop`
- `scripts/lint --desktop`
- `scripts/test --desktop`
- `lrh validate`

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-DESKTOP-RESTART-SHORTCUT` (resolved).

## Risk Notes

- Low impact: the gap needs two restart sources racing and a third press within one status poll.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/executions/WI-LRH-CONSOLE-DESKTOP-RESTART-SHORTCUT/`
