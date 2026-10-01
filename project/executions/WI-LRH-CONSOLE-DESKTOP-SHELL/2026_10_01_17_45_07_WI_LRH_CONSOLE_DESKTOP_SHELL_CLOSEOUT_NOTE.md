---
execution_id: 2026_10_01_17_45_07_WI_LRH_CONSOLE_DESKTOP_SHELL_CLOSEOUT_NOTE
prompt_id: PROMPT(WI-LRH-CONSOLE-DESKTOP-SHELL:WI_LRH_CONSOLE_DESKTOP_SHELL_CLOSEOUT_NOTE)[2026-10-01T17:45:07+00:00]
work_item: WI-LRH-CONSOLE-DESKTOP-SHELL
status: landed
rerun_of: 2026_10_01_02_37_31_WI_LRH_CONSOLE_DESKTOP_SHELL
pr: https://github.com/xenotaur/logical_robotics_harness/pull/762
commit: 3fed7dac2f5b3d82f487d3b8e86b96b10d4dd8b8
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/762"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-10-01T17:45:07+00:00
---

# Summary

This is the closeout note for PR #762, which implemented
`WI-LRH-CONSOLE-DESKTOP-SHELL`. The work ran through `/lrh-execute
WS-LRH-CONSOLE-LOCAL-DOGFOOD`, with `/lrh-implement` and then `/lrh-land`
inline. The owner approved adding the app icon at the run gate. The primary
record's body is immutable, so the chain note lives here.

# Result

CHAIN-NOTE: `cycles=2; stops=0; gates=[execute-chain, land-chain, owner-smoke, review-response, confirm-fixes, merge]; friction=network-push-retry; self_review_rounds=3; bot_rounds=1; note="The pre-push self-review found 2 should-fix issues. Quit could relaunch a queued action, and Exit panicked after a failed setup. Both were fixed before the first push. A venv-canonicalization bug was found during the scripted .app smoke and fixed. The owner's Mac smoke pass went 8/8. The first-push bots left 3 threads: Codex said to publish the shutdown latch before locking, Copilot said to validate PYTHONPATH as absolute, and Copilot's missing-record finding was already satisfied. The cold review then made the latch regression test deterministic. Merged with the SHA lock after 7/7 CI checks passed, both desktop jobs included."`

PR #762 merged as `3fed7dac2f5b3d82f487d3b8e86b96b10d4dd8b8`, using
`--match-head-commit 7509fe94`, after authorization in this session. Four
records landed with that commit: the primary, `_SELFREVIEW`, `_REVIEW`, and
`_CONFIRM`.

`WI-LRH-CONSOLE-DESKTOP-SHELL` is resolved and moved to `resolved/`. The
protocol reference now points to its resolved path.
`WI-LRH-CONSOLE-DESKTOP-SETTINGS`, `WI-LRH-CONSOLE-DESKTOP-DOGFOOD`, and
`WS-LRH-CONSOLE-LOCAL-DOGFOOD` stay `proposed`.

# Validation

- `lrh validate` was run after the closeout edits. See the closeout commit.

# Follow-up

Candidates for `WI-LRH-CONSOLE-DESKTOP-SETTINGS`:

- **Quit can stall during a launch.** Quit runs `shutdown()` on the main
  thread, so if a launch is in flight it can block until that launch finishes
  or times out. Show a "stopping" page, or stop off the main thread.
- **No visible link to Meta.** The owner found no link to the Meta view from
  the dashboard. Add a View > Meta menu item, or a small Serve change that
  links Meta from the dashboard.
- **Serve content can navigate to bundled pages.** That is harmless today,
  because those pages have no commands. Keep it in mind when Settings adds
  bundled pages with commands.

Owner impressions, as input for DOGFOOD, L1, and L2:

- Full-page loads were sometimes slow. Profile Serve rendering against the
  webview.
- The icon needs improvement; that is tracked elsewhere.
- The UX does not resemble the dependency-viewer mockups. L1 covers that;
  the mockups are in PR #737.
- The dashboard is long and completionist, which is good for debugging and
  poor for visibility. This is input for the console visual-language
  proposal.

Next: `/lrh-execute WS-LRH-CONSOLE-LOCAL-DOGFOOD` should resolve to
`WI-LRH-CONSOLE-DESKTOP-SETTINGS`.
