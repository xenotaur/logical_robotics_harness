---
execution_id: 2026_10_02_01_41_07_WI_LRH_CONSOLE_DESKTOP_SETTINGS_CLOSEOUT_NOTE
prompt_id: PROMPT(WI-LRH-CONSOLE-DESKTOP-SETTINGS:WI_LRH_CONSOLE_DESKTOP_SETTINGS_CLOSEOUT_NOTE)[2026-10-02T01:41:07+00:00]
work_item: WI-LRH-CONSOLE-DESKTOP-SETTINGS
status: landed
rerun_of: 2026_10_01_22_19_40_WI_LRH_CONSOLE_DESKTOP_SETTINGS
pr: https://github.com/xenotaur/logical_robotics_harness/pull/763
commit: abe0acf6bf9d67949927f6f1147526737daa5561
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/763"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-10-02T01:41:07+00:00
---

# Summary

This is the closeout note for PR #763, which implemented
`WI-LRH-CONSOLE-DESKTOP-SETTINGS`. The work ran through `/lrh-execute
WS-LRH-CONSOLE-LOCAL-DOGFOOD`, with `/lrh-implement` and `/lrh-land` inline. The
primary record's body is immutable, so the chain note lives here instead.

# Result

CHAIN-NOTE: `cycles=2; stops=0; gates=[execute-chain, land-chain, owner-smoke, review-response, confirm-fixes, merge]; friction=none; self_review_rounds=2; bot_rounds=1; note="The pre-push self-review found 3 should-fix bugs, all fixed before push: Cmd+Q bypassed ExitRequested via muda's terminate:, the server-details command blocked the UI, and saves under the env override defeated it. The owner ran a first-run Mac smoke pass from Finder with no config, and it passed. First-push bots left 4 threads, all fixed: the launch env conflict, workspace validation now mirroring find_project_dir, invalid env overrides kept active, and a truly non-blocking Exit stop. The cold review found it safe. Merged with a SHA lock after CI went 7/7 green."`

PR #763 merged as `abe0acf6bf9d67949927f6f1147526737daa5561`, using
`--match-head-commit 6662a7a1`, after authorization in this session. Four
records landed with that commit: the primary, `_SELFREVIEW`, `_REVIEW`, and
`_CONFIRM`.

`WI-LRH-CONSOLE-DESKTOP-SETTINGS` is resolved and has moved to `resolved/`.
The protocol reference now points to its resolved path.
`WI-LRH-CONSOLE-DESKTOP-DOGFOOD` stays `proposed`. It is now the next ready
item, because its dependency is resolved. `WS-LRH-CONSOLE-LOCAL-DOGFOOD` stays
`proposed`.

# Validation

- `lrh validate` was run after these closeout edits. See the closeout commit.

# Follow-up

Low-severity items deferred from the final cold review:

- Under the developer env override, a browser-choice change applies
  immediately, but the UI says saved settings take effect later.
- With an invalid env override, the Settings page should tell the user to
  unset the variables, since saving cannot fix it.
- (nit) A dead `let _ = pid;` remains in `try_shutdown_never_waits_for_an_in_flight_launch`.

Input for `WI-LRH-CONSOLE-DESKTOP-DOGFOOD`:

- External-link handoff was not exercised by hand, because Serve pages
  contain no external links. Checklist step 6 covers it if such links appear.
- The owner noted that most work items were not prompt-ready, so the
  workbench prompt download was not useful. That is a planning-data quality
  issue, not an app issue. It is input for the sessions and for L1.
- Earlier SHELL impressions still apply: slow full-page loads, a long
  completionist dashboard, and the gap from the dependency-viewer mockups.
- The owner's saved configuration currently serves the
  `lrh-console-desktop-protocol-b156e4` worktree. Point it at the main
  checkout in Settings before the dogfood sessions.

Next: `/lrh-execute WS-LRH-CONSOLE-LOCAL-DOGFOOD` should resolve to
`WI-LRH-CONSOLE-DESKTOP-DOGFOOD`, the owner's five recorded Mac sessions.
