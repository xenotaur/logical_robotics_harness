---
execution_id: 2026_10_01_22_35_07_WI_LRH_CONSOLE_DESKTOP_SETTINGS_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_SETTINGS_REVIEW)[2026-10-01T22:35:07+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/763
commit: 
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/763"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-10-01T22:35:07+00:00
---

# Summary

Review-response round 1 for PR #763 (`WI-LRH-CONSOLE-DESKTOP-SETTINGS`), run as
part of `/lrh-execute` → `/lrh-land`. CI on the first push passed 7/7. The
hosted reviews left 4 inline threads, one from Codex and three from Copilot.
The user chose to fix all four.

# Result

All four were fixed in `88272e5d`:

1. **Codex P2: `run launch` passed both launch forms.** The command inherited
   an exported `LRH_CONSOLE_LRH_EXECUTABLE` alongside the Python form it
   sets, and the app rejects having both. It now runs
   `env -u LRH_CONSOLE_LRH_EXECUTABLE …`, and the dry-run test asserts this.
2. **Copilot: the workspace check was weaker than the backend's.** Settings
   accepted any directory containing `project/`, while the backend's
   `lrh.control.loader.find_project_dir` requires `focus/` and `work_items/`.
   `is_lrh_workspace` now mirrors the loader exactly. The test fixture was
   updated, and a new test checks that an empty `project/` is rejected.
3. **Copilot: an invalid `LRH_CONSOLE_*` override was treated as "none".** As
   a result, a later save took over the session. The invalid override now
   stays classified as `Environment`, its problem stays visible, and saves
   only write the file.
4. **Copilot: `try_shutdown` could still wait about 15 s on an idle child.**
   It now sends `shutdown` through the new `OwnedServer::request_stop`,
   closes stdin, and returns without waiting. The child then stops on its
   own after the app exits.
   - New test:
     `try_shutdown_of_an_idle_real_backend_lets_it_exit_on_its_own`.
   - Updated test: `try_shutdown_never_waits_for_an_in_flight_launch`, which
     now asserts no wait in the idle case too.

# Validation

- `cargo test --locked`: 27 unit, 9 capability, and 22 supervisor tests
  passed.
- `scripts/format --check --diff --desktop`, `scripts/lint --desktop`,
  `scripts/test --desktop`, `lrh validate`, and `scripts/check-workflows`
  all passed.

# Follow-up

Next is confirm-fixes: resolve the 4 threads, run a substitute cold review of
the new HEAD, and re-check CI.
