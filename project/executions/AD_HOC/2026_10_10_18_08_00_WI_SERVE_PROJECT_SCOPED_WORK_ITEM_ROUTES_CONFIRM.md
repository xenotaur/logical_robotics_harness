---
execution_id: 2026_10_10_18_08_00_WI_SERVE_PROJECT_SCOPED_WORK_ITEM_ROUTES_CONFIRM
prompt_id: PROMPT(AD_HOC:WI_SERVE_PROJECT_SCOPED_WORK_ITEM_ROUTES_CONFIRM)[2026-10-10T18:07:38+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_10_10_05_32_46_WI_SERVE_PROJECT_SCOPED_WORK_ITEM_ROUTES
pr: https://github.com/xenotaur/logical_robotics_harness/pull/818
commit: 08bf5cfbeda32c1edf3d172248f2080798ad83f1
created_at: 2026-10-10T18:08:00+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/818
session_transcript: claude-app:c94e499e-da6e-4e3f-a979-5876278e9f67
---
# Summary

Confirm-fixes pass for PR 818, run inline from `/lrh-land` Step 5. It
verified the review-response fixes against HEAD
`215ddd2958a1248f49e11878a0ada5ff228857f6`.

# Result

A cold-context subagent classified the threads (`--subagent`, offered
because this session authored the fixes). It also checked every code
citation in the work item against `src/lrh/serve.py` and
`tests/cli_tests/serve_test.py` and found them all accurate.

Resolved threads, all from bots:

- `PRRT_kwDOR7l1D86rBZZZ`, copilot-pull-request-reviewer:
  **Clear-satisfied**. The preview page's navigation links are now in every
  section, scoped to `/project/<id>/...`.
- `PRRT_kwDOR7l1D86rBbf5`, chatgpt-codex-connector: **Clear-satisfied**. The
  409 is limited to routes that use `_config_for_project_selector`. The
  Non-Goals keep the dashboard, design, and workstream routes, which use
  `_project_from_meta_selector`, at 404.
- `PRRT_kwDOR7l1D86rBbf9`, chatgpt-codex-connector: **Clear-satisfied**. The
  work item is listed in `WS-LRH-CONSOLE-LOCAL-DOGFOOD` line 40, from commit
  `0843436d`.

Surfaced exceptions: none.

`confirm_fixes_batch: auto_unless_unusual`.
`lrh confirm-fixes check-batch-routine` exited 0 ("all 3 thread(s) are
Clear-satisfied").

The subagent noted two things that are not contradictions:

- Scope and tests include HEAD returning 409 on the dependency-map routes,
  but neither acceptance list states it.
- The scoped "Back to viewer context" target is the project dashboard, not a
  work-item anchor.

Thread-resolution verdict (Step 6): **green**.

# Validation

- The authoritative unresolved-thread list (`isResolved == false`) is empty
  after resolution.
- No CI checks run on this branch, and `main` has no required-status-check
  rule.

# Follow-up

- Step 8: run REVIEW-LANDED on this record's commit.
