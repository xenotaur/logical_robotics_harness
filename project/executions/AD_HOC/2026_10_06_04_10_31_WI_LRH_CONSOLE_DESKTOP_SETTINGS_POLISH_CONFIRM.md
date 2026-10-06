---
execution_id: 2026_10_06_04_10_31_WI_LRH_CONSOLE_DESKTOP_SETTINGS_POLISH_CONFIRM
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_SETTINGS_POLISH_CONFIRM)[2026-10-06T04:10:31+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_10_06_03_54_48_WI_LRH_CONSOLE_DESKTOP_SETTINGS_POLISH
pr: https://github.com/xenotaur/logical_robotics_harness/pull/776
commit: b1f97272a64bbd0872c7af1d6fd7c3530a4e8fe4
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/776"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-10-06T04:10:31+00:00
---

# Summary

This record covers `/lrh-confirm-fixes` for PR #776
(`WI-LRH-CONSOLE-DESKTOP-SETTINGS-POLISH`), run inline from `/lrh-land`
after review-response round 1 (`f181266c`) and a follow-up (`a3bf2c82`).

# Result

**Threads.** The authoritative list has 1 thread, resolved with
`resolveReviewThread`: Copilot, "Run initial scroll and highlight after
settings and details load". It is Clear-satisfied on HEAD:
`loadSettings().then(loadDetails).finally(...)` shows the initial section
after both loads.

**Substitute cold review of `b4cf646d..e80cfd1f`** (hosted bots reviewed
`93a10bbd`). Verdict: safe to merge.

- It checked the full-height grid and flex layout by reading the rules:
  - a hidden `#problem` row collapses;
  - explicit placement in row 4;
  - a definite `100vh` height;
  - columns scroll on their own;
  - the minimum width of 47rem is below the 52rem fallback breakpoint;
  - the fallback restores normal page flow;
  - `index.html` is unaffected.
- It confirmed the `.finally()` handling and that the contract test still
  holds.
- Should-fix, applied in `a3bf2c82`: with the page no longer scrolling,
  `scrollIntoView` could not reset a column that had scrolled on its own.
  `lrhShowSection` now also resets the scroll of the form or the details
  column.
- Nits applied: long paths in the full-width notes wrap, and the duplicate
  `h1` rule was merged.
- Nits left: focus-ring clipping at the column edges, worth a glance in the
  owner check, and the flash covering only the visible part of a scrolled
  column. Both are cosmetic.

**Owner's Mac check, 2026-10-06, on `b4cf646d`:**

1. Settings showed on the left and the server details on the right, both
   visible.
2. Server Details flashed.
3. With the window closed, Settings appeared and Server Details flashed.
4. The symlink note showed.
5. "Recent server output doesn't quite fit", with a screenshot. Fixed in
   `f181266c` and `a3bf2c82`.

The owner's re-check of step 5 on the new code was pending when this record
was written. It goes in the closeout note.

**Verdict:** green on threads and review. The merge waits for CI on the
final commit and for the owner's step-5 re-check.

# Validation

- `cargo test --lib`: 42 tests passed.
- `scripts/format --check --diff --desktop` passed.
- `scripts/lint --desktop` passed.
- `apps/desktop/scripts/run bundle` built the app.
- `lrh validate`: 0 errors.

# Follow-up

Next is the single ask for merge and closeout.
