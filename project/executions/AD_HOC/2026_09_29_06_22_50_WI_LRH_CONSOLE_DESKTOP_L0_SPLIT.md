---
execution_id: 2026_09_29_06_22_50_WI_LRH_CONSOLE_DESKTOP_L0_SPLIT
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_L0_SPLIT)[2026-09-29T06:15:01+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/757
commit: 46fb214be36d74b4f20e857045b0a1b8a4757912
agent: "claude_app"
instruction_source: "project/work_items/resolved/WI-LRH-CONSOLE-DESKTOP-L0.md"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-09-29T06:22:50+00:00
---

# Summary

This is the planning split of `WI-LRH-CONSOLE-DESKTOP-L0`, run through
`/lrh-work-item`. After PR #750 merged, the user noted that one work item was
spanning several PRs, where the usual pattern is a workstream whose work items
each map to one PR. The user approved narrowing L0 to what PR #750 delivered
and moving the rest of its scope into three new work items under
`WS-LRH-CONSOLE-LOCAL-DOGFOOD`.

# Result

- `WI-LRH-CONSOLE-DESKTOP-L0` is now in `project/work_items/resolved/`.
  - It is narrowed to the toolchain, the `--desktop` scripts, desktop CI, the
    sdist/wheel guards, and the minimal Tauri app.
  - Its resolution cites PR #750, merge `9eeea442`, and closeout `4f0f7a51`.
  - A new "Scope split" section maps the original items to their successors.
- New `WI-LRH-CONSOLE-DESKTOP-SUPERVISOR` (deliverable): original item 2, the
  Rust supervisor with no UI and `supervisor_test.rs`. It depends on PROTOCOL
  and L0.
- New `WI-LRH-CONSOLE-DESKTOP-SHELL` (deliverable): original items 1 and 3–7,
  plus the documentation and capability-test half of item 8 and the three test
  items deferred from PR #750. It depends on SUPERVISOR.
- New `WI-LRH-CONSOLE-DESKTOP-DOGFOOD` (operation): the evidence half of
  item 8, meaning the five Mac sessions, the checklist, and
  `EV-LRH-CONSOLE-DESKTOP-L0-DOGFOOD`. It depends on SHELL.
- `WS-LRH-CONSOLE-LOCAL-DOGFOOD`: `work_items:` now lists PROTOCOL, L0,
  SUPERVISOR, SHELL, and DOGFOOD in that order, and the Work Items section is
  updated. The L0 decision gate is unchanged.
- `apps/README.md` and `docs/reference/desktop-server-protocol.md` now point
  at the new consumer work items.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items readiness` returns `prompt_ready: yes`, with no warnings,
  for SUPERVISOR, SHELL, and DOGFOOD.
- `scripts/test`: pass.
- The pre-mint slug check found no prior record.

# Follow-up

- Open question for DOGFOOD: should the five sessions cover LCATS as well as
  LRH?
- Next implementation run: `/lrh-execute WS-LRH-CONSOLE-LOCAL-DOGFOOD`, which
  should resolve to `WI-LRH-CONSOLE-DESKTOP-SUPERVISOR`.
