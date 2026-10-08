---
execution_id: 2026_10_08_06_17_12_LRH_CONSOLE_FRAME_REVIEW
prompt_id: PROMPT(WI-LRH-CONSOLE-FRAME:LRH_CONSOLE_FRAME_REVIEW)[2026-10-08T06:17:12+00:00]
work_item: WI-LRH-CONSOLE-FRAME
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/792
commit: bf4f8f248e15e2319d6adce9c777c3f54db105f3
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/792"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-10-08T06:17:12+00:00
---


# Summary

This record covers review-response round 1 for PR #792 (`WI-LRH-CONSOLE-FRAME`), run as part of
`/lrh-land` inside `/lrh-execute`.

- **CI** passed 7/7 on `83a3d3e5`.
- **Codex** reviewed `90b6c16b` and left no findings.
- **Copilot** reviewed `83a3d3e5` and left 1 thread.
- **The owner's decision:** "Yes, apply it".
- **The owner's Mac check** of this branch's app, built from this worktree with
  `apps/desktop/scripts/run bundle`, then `launch`:
  - "Gear opens setting, main window doesn't change";
  - opening and closing Settings "work fine";
  - "LRH icon goes to statusboard; collapse item works";
  - not checked in a browser.

# Result

Fixed in `05deca2b`.

1. **Copilot, `src/lrh/serve.py`: unloadable projects were dropped from the scope switcher.**
   `_frame_projects` now lists every `MetaProjectLoadResult` by its `registry_name`, labelled
   with the record's `display_name` when it loads. So a broken entry stays reachable, matching
   its unavailable card on `/meta`. Added
   `test_scope_switcher_lists_projects_whose_records_fail_to_load`.

# Validation

- `scripts/format --check --diff` and `scripts/lint` pass.
- `tests.cli_tests.serve_test` and `tests.ux_tests.frame_test` pass (103 tests).
- `git diff --check` is clean.

# Follow-up

Next is confirm-fixes: resolve the thread, then re-check CI.
