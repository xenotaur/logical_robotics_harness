---
execution_id: 2026_10_05_20_20_18_WI_LRH_CONSOLE_DESKTOP_SHELL_POLISH_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_SHELL_POLISH_SELFREVIEW)[2026-10-05T20:20:18+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/771
commit: 
agent: "claude_app"
instruction_source: "project/work_items/proposed/WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH.md"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-10-05T20:20:18+00:00
---

# Summary

This record covers the pre-push `/lrh-self-review` of the
`WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH` branch: three rounds by one
cold-context general-purpose subagent, which only reported findings. Round 1
reviewed `0343dc3f`, round 2 the delta to `a9999c1e`. The invoking session
applied the fixes, ending at `2a228aee`.

# Result

**Round 1 at `0343dc3f`: needs fixes.** Nothing was blocking, and the safety
boundary held. The reviewer confirmed:

- the restart, crash, and race sequences;
- the locking;
- that the main window still gets no permissions;
- that the accelerators parse.

Should-fix findings, both fixed in `a9999c1e`:

1. **D7 was incomplete.** "Incompatible backend", "Backend program", and the
   how-to still said "backend". All are now "server".
2. **History went wrong after native or rapid navigation.** `visited()` now
   takes a navigation to `back.last()` or `forward.last()` as that move.

Nits:

- Applied:
  - dead `pending` state, removed;
  - same-port restart and Quit now end the history, by resetting on any
    navigation outside the origin;
  - the subframe limitation is documented;
  - the unused `Clone` impl is removed.
- Not applied:
  - refreshing the items after a no-op press. The reviewer confirmed this is
    sound in round 2: every loss of the server navigates to a status page,
    which disables the items.
  - `MainWindowHistory` and `handle_menu` tests, which would need menus under
    MockRuntime.

**Round 2 at `a9999c1e`: safe to push.** Both should-fix items were
confirmed resolved.

- A new should-fix: in-page anchor links were misread as Back. Fixed in
  `2a228aee` by recording pages without fragments, with a test.
- A nit, documented as a trade-off: a link to the previous page acts as Back.
- An observation about existing behavior: the webview's own Back can show a
  status page. It is noted in the PR as out of scope.

# Validation

At `2a228aee`:

- `cargo test --lib`: 35 tests passed.
- clippy (`-D warnings`): clean.
- `scripts/test --desktop`: passed.
- `lrh validate`: 0 errors.

# Follow-up

None for this record.
