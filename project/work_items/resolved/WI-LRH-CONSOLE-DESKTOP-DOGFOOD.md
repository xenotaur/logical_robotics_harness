---
id: "WI-LRH-CONSOLE-DESKTOP-DOGFOOD"
title: "Dogfood the LRH Console Mac app for five recorded sessions"
type: "operation"
status: "resolved"
blocked: false
blocked_reason: null
resolution: 'Completed in PR #766 (commit db8c784c). project/evidence/EV-LRH-CONSOLE-DESKTOP-L0-DOGFOOD.md records nine real owner Mac sessions and the full manual checklist, including forced startup failure, backend crash, and app crash recovery, plus a recommendation: close L0; L1 proceeds with adjustments; L3 stays gated. The L0 gate closed with two recorded owner waivers. Waiver 1 covers the Chrome-absent fallback, forced workspace mismatch, and external-link handoff. Waiver 2 accepts day-level dates and a recalled Dock launch for session 2. The waived checks are tracked in the design backlog. Code defects were filed as WI-SERVE-QUIET-CLIENT-DISCONNECT, WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH, and WI-LRH-CONSOLE-DESKTOP-SETTINGS-POLISH.'
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
- "WI-LRH-CONSOLE-DESKTOP-SETTINGS"
blocked_by: []
expected_actions:
- "create_file"
- "edit_file"
- "run_tests"
- "create_report"
- "create_pr"
forbidden_actions:
- "force_push"
- "delete_branch"
- "merge_pr"
- "publish_package"
- "deploy_remote_service"
- "implement_project_mutation"
- "run_lrh_agentic"
- "fabricate_dogfood_sessions"
acceptance:
- "Five real Mac sessions are recorded, each opened from the Dock with no terminal server startup after the explicit initial setup. Each record gives the date, app and backend versions, actions taken, result, and remaining friction."
- "The manual checklist in docs/how-to/lrh-console-local-dogfood.md is run on the target Mac. That covers Dock, menus, keyboard, close/reopen, Stop/Restart/Quit, crash recovery, browser handoff, and workspace mismatch, with real results."
- "The evidence shows that a separately started server stays untouched by Stop, Restart, Quit, and failure, and that CLI use stays intact."
- "project/evidence/EV-LRH-CONSOLE-DESKTOP-L0-DOGFOOD.md follows the evidence schema. It records the actual test commands and results, failures, friction, the embedded-versus-Chrome interaction matrix, and a recommendation for L1 and L3."
- "Automated Linux checks alone do not close this item. Every limitation is recorded rather than hidden."
required_evidence:
- "manual_review"
- "lrh_validate"
- "test_output"
- "validation_output"
artifacts_expected:
- "project/evidence/EV-LRH-CONSOLE-DESKTOP-L0-DOGFOOD.md"
- "Small fixes to docs/how-to/lrh-console-local-dogfood.md found during the sessions (documentation only)"
---

# LRH Console L0 Mac dogfood

## Summary

Use the LRH Console Mac app in five real working sessions, run the manual
checklist, and record the evidence and a recommendation for L1 and L3. This is
the L0 evidence gate in `WS-LRH-CONSOLE-LOCAL-DOGFOOD`.

## Problem / Context

This item was split out of `WI-LRH-CONSOLE-DESKTOP-L0` (the evidence half of
its Required Changes item 8), so that code deliverables are not held open by
an operation.

The workstream's decision-gate table requires "Protocol failure tests and five
terminal-free macOS sessions, including close/reopen, crash recovery,
Stop/Restart/Quit, and browser handoff" before L1 advances. Automated tests
cannot prove Mac Dock, menu, and keyboard behavior: Tauri documents that
macOS has no desktop WebDriver client, and its WebdriverIO route needs Node.

### Duplication search

- In-repo: `project/evidence/EV-LRH-CONSOLE-DESKTOP-PROTOCOL.md` is the schema
  and style reference. No dogfood evidence for the desktop app exists yet.
- Recommendation: proceed.

### Demand search

- Work items: this item closes the L0 evidence gate that the former
  `WI-LRH-CONSOLE-DESKTOP-L0` acceptance criteria required.
- Recommendation: proceed.

## Scope

- Five real use sessions and one full manual checklist run on the target Mac.
- One evidence record, plus documentation fixes the sessions reveal.
- Code defects found during the sessions become new work items. They are not
  fixed under this item.

## Required Changes

1. Build the app on the target Mac with the commands in
   `docs/how-to/lrh-console-local-dogfood.md`, and complete the explicit
   first-run setup.
2. Record five real working sessions. Each opens from the Dock, with no
   terminal server startup. For each, record the date, app and backend
   versions, actions taken, result, and remaining friction.
3. Run the full manual checklist:
   - Dock launch;
   - menus and keyboard shortcuts;
   - close and reopen;
   - Start, Stop, Restart, and Quit;
   - app crash and backend crash recovery;
   - browser handoff and the Chrome-absent fallback;
   - workspace mismatch;
   - a separately started server staying untouched.
4. Write `project/evidence/EV-LRH-CONSOLE-DESKTOP-L0-DOGFOOD.md` using the
   evidence schema. Include the actual test commands and results, failures
   and friction, the embedded-versus-Chrome interaction matrix, and a
   recommendation for L1 and L3.
5. File a work item for each code defect found, and link it from the
   evidence record.

## Non-Goals

- Do not change app or backend code under this item. Record defects as new
  work items instead.
- Do not substitute automated Linux checks or synthetic runs for the real Mac
  sessions.
- Do not start L1 graph work.

## Acceptance Criteria

- Five real Mac sessions are recorded from the Dock, with no terminal server
  startup after setup.
- The full manual checklist has been run with real results.
- The evidence shows that unrelated servers stay untouched and that CLI use
  stays intact.
- The evidence record follows the schema and includes a recommendation for L1
  and L3.
- Automated Linux checks alone do not close this item, and limitations are
  recorded.

## Validation

- `lrh validate`
- `scripts/test --desktop` on the target Mac (record the output in the evidence)
- Run the manual checklist in `docs/how-to/lrh-console-local-dogfood.md` on the target Mac.

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-DESKTOP-SETTINGS`, which completes the app and
  writes the how-to and checklist these sessions follow.
- Its evidence gates the L1 work items in `WS-LRH-CONSOLE-LOCAL-DOGFOOD`.

## Risk Notes

- Sessions can pass without exercising failure paths. The checklist's crash
  and mismatch cases must be forced deliberately, not waited for.
- Sessions must be real use by the human owner. An agent may help draft the
  evidence record from the owner's notes, but must not invent sessions or
  results.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md`

## Open Questions

Decide whether the five sessions should cover both LRH and LCATS workspaces,
or LRH only, before the first session.
