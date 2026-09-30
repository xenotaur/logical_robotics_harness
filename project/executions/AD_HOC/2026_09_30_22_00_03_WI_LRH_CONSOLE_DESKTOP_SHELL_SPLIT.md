---
execution_id: 2026_09_30_22_00_03_WI_LRH_CONSOLE_DESKTOP_SHELL_SPLIT
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_SHELL_SPLIT)[2026-09-30T22:00:03+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
agent: "claude_app"
instruction_source: "project/work_items/proposed/WI-LRH-CONSOLE-DESKTOP-SHELL.md"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-09-30T22:00:03+00:00
---

# Summary

Planning split of `WI-LRH-CONSOLE-DESKTOP-SHELL`.

`/lrh-execute WS-LRH-CONSOLE-LOCAL-DOGFOOD` resolved to SHELL. SHELL was
ready, with no warnings. Before implementation, the user chose "Split first",
following SHELL's own risk note: split at the configuration/recovery boundary
rather than land several PRs under one item. That execute run stopped before
its chain gate. It is recorded in the run journal as an early stop.

# Result

- **`WI-LRH-CONSOLE-DESKTOP-SHELL`**, narrowed. It keeps:
  - the main window, with the owned Serve origin or one minimal bundled
    status page;
  - native Server Start/Stop/Restart and View Dashboard/Reload menus, run
    off the UI thread and serialized;
  - Mac close, reopen, and Quit behavior;
  - navigation and capability boundaries, where popups and external links
    are refused;
  - `capability_boundaries_test.rs`;
  - developer-only launch settings, with no PATH lookup.

  It also carries the three deferred PR #750 test nits, plus the two Start
  edge cases deferred from PR #758. A new forbidden action,
  `implement_lrh_console_desktop_settings`, keeps SETTINGS work out of it.
- **`WI-LRH-CONSOLE-DESKTOP-SETTINGS`**, new. It covers:
  - private configuration and first-run setup;
  - the Settings/Details window;
  - the five recovery pages;
  - browser handoff: Open in Chrome, external links, and the fallback;
  - the narrow Settings-window capability, with extended tests;
  - `docs/how-to/lrh-console-local-dogfood.md` and its checklist.

  It depends on SHELL.
- **`WI-LRH-CONSOLE-DESKTOP-DOGFOOD`** now depends on SETTINGS.
- **The workstream**, `WS-LRH-CONSOLE-LOCAL-DOGFOOD`:
  - `work_items:` is now … SUPERVISOR, SHELL, SETTINGS, DOGFOOD;
  - the Work Items section is updated;
  - the L0 gate is unchanged.
- **Other references.** The proposal's initial-items list, the consumer
  lines in the protocol reference, and `apps/README.md` all name the new
  item. The module doc in `apps/desktop/src-tauri/src/lib.rs` is left for the
  SHELL implementation, so this planning PR does not touch app code.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items readiness`: `prompt_ready: yes`, with no warnings, for
  SHELL, SETTINGS, and DOGFOOD.
- `scripts/test`: pass.
- Pre-mint slug check: no prior record.

# Follow-up

- Land this PR, then re-run `/lrh-execute WS-LRH-CONSOLE-LOCAL-DOGFOOD`, which
  should resolve to the narrowed SHELL.
