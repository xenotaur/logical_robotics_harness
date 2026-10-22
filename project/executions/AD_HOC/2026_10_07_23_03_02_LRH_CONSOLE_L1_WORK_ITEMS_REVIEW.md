---
execution_id: 2026_10_07_23_03_02_LRH_CONSOLE_L1_WORK_ITEMS_REVIEW
prompt_id: PROMPT(AD_HOC:LRH_CONSOLE_L1_WORK_ITEMS_REVIEW)[2026-10-07T23:02:45+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/782
commit: 6c34bc11956088c5e5d5308630bd042922fa741d
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/782"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-10-07T23:03:02+00:00
---


# Summary

This record covers review-response round 1 for PR #782 (the eight LRH Console L1 work items),
run as part of `/lrh-land`.

- **CI** passed 5/5 on `7af3c9e8`.
- **Codex** left 4 threads; **Copilot** left 7. One Copilot thread repeats Codex's P1.
- **The owner's decision:** "Apply them", covering all eleven fixes as proposed, including the
  two decisions on the L1 gate and theme precedence.

# Result

All eleven were fixed in `b9bf48bc`.

1. **Codex P1 and Copilot (duplicates), L1-DOGFOOD.** The three questions must span LRH and
   LCATS, with at least one answered on the LCATS map. An LCATS gap is linked in `blocked_by`
   and blocks the item; LRH alone never passes the gate.
2. **Codex P2, INTERACTIVE.** An explicit `--theme light` or `--theme dark` wins, and the in-page
   switch is hidden in that case. It appears only under `system`. Tagged *(recommended)* and
   added to acceptance.
3. **Codex P2, MAP-STATIC.** Table IDs are ordinary links to `?item=<id>`, styled as buttons.
4. **Codex P2, FRAME.** The chosen icon library's license (Lucide ISC or Phosphor MIT) ships
   with the icons, and is added to acceptance and artifacts.
5. **Copilot, MAP-SNAPSHOT.** The contracts are now fixed:
   `GET /api/project/<project_id>/dependency-maps/<view>` and
   `lrh dependency-map snapshot <view> [--project-root PATH]`, with their error behavior. Both
   are in acceptance and artifacts.
6. **Copilot, MAP-STATIC.** Added a first step that evaluates established layout and rendering
   libraries, with no layout engine from scratch (dogfood proposal `:71-73`, `:407-408`). The
   evaluation is also an acceptance item.
7. **Copilot, STATUSBOARD.** Added the script-free band collapse to both acceptance lists.
8. **Copilot, FRAME, INTERACTIVE and THEME artifacts.** Added `tests/cli_tests/serve_test.py`,
   `docs/reference/cli/serve.md` and `apps/desktop/src-tauri/tests/supervisor_test.rs` where
   each item requires them.

Also removed a doubled blank line in the primary execution record.

# Validation

- `lrh validate`, run from this worktree's `src`: 0 errors, 0 warnings.
- `lrh work-items readiness` reports `prompt_ready: yes` for all eight.
- `git diff --check` is clean.

# Follow-up

Next is confirm-fixes: verify and resolve the 11 threads, then re-check CI.
