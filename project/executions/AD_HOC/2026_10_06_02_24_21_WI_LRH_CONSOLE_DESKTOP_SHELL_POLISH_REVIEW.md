---
execution_id: 2026_10_06_02_24_21_WI_LRH_CONSOLE_DESKTOP_SHELL_POLISH_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_SHELL_POLISH_REVIEW)[2026-10-06T02:24:21+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/771
commit: 
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/771"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-10-06T02:24:21+00:00
---

# Summary

This record covers review-response round 1 for PR #771
(`WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH`), run as part of `/lrh-land`. The
hosted reviews left 3 inline threads, one from Codex on `2a228aee` and two
from Copilot on `7fda1595`. The owner chose to fix all three, as proposed.

**CI stop.** The landing chain had stopped first, under the stop-work
condition, on failing CI. Every failed job on `2a228aee` and `7fda1595` had
been cancelled after about 15 minutes in the queue, with no runner ever
assigned. That was GitHub runner availability, not a test failure: every job
that got a runner passed. The fix push triggers fresh CI.

# Result

All three were fixed in `391aea6b`:

1. **Codex P2: a phantom history entry for download links.** A `?download=1`
   link reaches the navigation handler before WebKit treats it as a
   download, so it was recorded as the current page while the screen never
   changed.
   - `PageHistory` now keeps the stacks from before the last new-page
     record.
   - The main window's download handler calls `download_started(url)`,
     which restores them when that URL is current.
   - Test: `a_navigation_that_becomes_a_download_is_undone`.
2. **Copilot: menu dispatch and the policy re-check were untested.** The
   logic moved into `history_direction(id)` and `history_target(pages,
   policy, back)`, which `handle_menu` now calls.
   - Test `menu_items_map_to_history_directions` covers the mapping.
   - Test `history_moves_only_to_pages_the_current_policy_allows` covers
     the policy: an old port is refused, a stopped server is refused, and
     Back and Forward land on the right pages.
3. **Copilot: Server Details still said "backend".** Its Last error row
   shows `SupervisorError` messages verbatim. The eight user-visible
   messages in `apps/desktop/src-tauri/src/supervisor.rs` now say "the
   server" or "no running server". Machine codes are unchanged. The Python
   reference supervisor (`src/lrh/desktop_supervisor.py`) is CLI tooling,
   not app UI, and was left as is.

# Validation

- `scripts/format --check --diff --desktop` passed.
- `scripts/lint --desktop` passed.
- `scripts/test --desktop --log`: `Ran 1909 tests`, OK. Rust: 38 unit, 9
  capability, and 22 supervisor tests passed.
- `lrh validate`: 0 errors, 0 warnings.
- `apps/desktop/scripts/run bundle` built the app.

# Follow-up

Next is confirm-fixes: resolve the 3 threads, run a substitute review of the
new HEAD, re-check CI, and record the owner's manual Mac check.
