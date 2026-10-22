---
execution_id: 2026_10_06_03_36_45_WI_LRH_CONSOLE_DESKTOP_SHELL_POLISH_CLOSEOUT_NOTE
prompt_id: PROMPT(WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH:WI_LRH_CONSOLE_DESKTOP_SHELL_POLISH_CLOSEOUT_NOTE)[2026-10-06T03:36:45+00:00]
work_item: WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH
status: landed
rerun_of: 2026_10_05_20_20_18_WI_LRH_CONSOLE_DESKTOP_SHELL_POLISH
pr: https://github.com/xenotaur/logical_robotics_harness/pull/771
commit: 356615f8b5bafecfc4f014289e0e59ec0ce08446
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/771"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-10-06T03:36:45+00:00
---

# Summary

This is the closeout note for PR #771, which implemented
`WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH`. The work ran through `/lrh-execute
WS-LRH-CONSOLE-LOCAL-DOGFOOD`, with `/lrh-implement` and `/lrh-land` inline.
The primary record's body is immutable, so the chain note and the owner's
manual-check results live here.

# Result

CHAIN-NOTE: `cycles=2; stops=1; gates=[execute-chain, land-chain, ci-stop, review-response, merge]; friction=ci-runners; self_review_rounds=4; bot_rounds=1; note="The owner chose an app-side PageHistory over webview history. Pre-push cold review took three rounds: D7 was completed, the history was kept consistent with native and rapid moves, and anchor links were stripped of fragments. The first CI stopped the chain, because GitHub cancelled jobs with no runner assigned. Bots raised 3 valid findings, all fixed: download navigations are undone, menu dispatch and the policy re-check are tested, and Server Details errors say server. The substitute review was safe. CI went 7/7 green, the owner's manual Mac check passed, and the merge was SHA-locked."`

PR #771 merged as `356615f8b5bafecfc4f014289e0e59ec0ce08446`, using
`--match-head-commit f042f826`, after authorization in this session. Four
records landed with that commit: the primary, `_SELFREVIEW`, `_REVIEW`, and
`_CONFIRM`.

**Owner's manual Mac check.** The owner ran `apps/desktop/scripts/run
launch` on 2026-10-06 and reported:

1. Back and Forward were greyed out. After a link was clicked, Back became
   available. Back returned, Forward then became available, and Forward
   worked.
2. Back (⌘[) and Forward (⌘]) from `/health` worked.
3. Restart showed "Starting…", and Back and Forward were greyed out.
4. Right after the restart, ⌘[ did nothing, because the history had been
   reset and no page had been visited yet. "After futzing around, behavior
   seemed to be as expected."
5. The prompt Markdown download worked as expected.
6. ⌘Q worked as expected.

`WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH` is resolved and has moved to
`resolved/`. The L0 dogfood evidence record's artifact link now points to
the resolved path. `WS-LRH-CONSOLE-LOCAL-DOGFOOD` stays `active`, with
`WI-LRH-CONSOLE-DESKTOP-SETTINGS-POLISH` open.

# Validation

- `lrh validate` was run after these closeout edits. See the closeout commit.

# Follow-up

- Optional: decide whether to disable the webview's native Delete-key Back in
  the main window, so it never shows a status page. That behavior predates
  this work.
- Next: `/lrh-execute WS-LRH-CONSOLE-LOCAL-DOGFOOD` should resolve to
  `WI-LRH-CONSOLE-DESKTOP-SETTINGS-POLISH`.
