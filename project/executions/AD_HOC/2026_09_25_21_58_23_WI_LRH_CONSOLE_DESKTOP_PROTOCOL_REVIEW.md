---
execution_id: 2026_09_25_21_58_23_WI_LRH_CONSOLE_DESKTOP_PROTOCOL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_PROTOCOL_REVIEW)[2026-09-25T21:52:36+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_09_25_21_28_56_WI_LRH_CONSOLE_DESKTOP_PROTOCOL
pr: https://github.com/xenotaur/logical_robotics_harness/pull/727
commit: 
created_at: 2026-09-25T21:58:23+00:00
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/727"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
---

# Summary

This is the review-response round for PR #727
(`WI-LRH-CONSOLE-DESKTOP-PROTOCOL`), run inline from `/lrh-land` Step 4
inside a human-initiated `/lrh-execute` chain. It covers five unresolved
threads: three from `chatgpt-codex-connector` and two from
`copilot-pull-request-reviewer`. The user confirmed addressing all five at
the Step 4 gate.

# Result

All five threads passed the presence, validity, and feasibility checks. They
were fixed in commit `96fa78b0`:

1. **Codex P2, stale handshake after child exit.** Added
   `OwnedServer.is_running()`, which checks the child handle.
   `DesktopSupervisor.start()` now reaps an exited child and relaunches.
   Covered by smoke test `test_start_after_child_crash_relaunches` and unit
   test `test_exited_child_is_not_running`.
2. **Codex P2, control-directory identity.** `verify_ready` now requires the
   reported `project_root` and `project_dir` to agree with each other and
   with the configured path, through `_workspace_matches`. Covered by two new
   unit tests.
3. **Codex P2, boolean `protocol_version` in `ready`.** Added a shared
   `desktop_protocol.is_supported_version()` that rejects JSON booleans; the
   supervisor now uses it.
4. **Copilot, self-check on a non-object payload.** A non-object status
   payload now raises `startup_self_check_failed` and the server is closed.
   The "also line 817" note, a boolean version in child control messages,
   now uses `is_supported_version`. Covered by unit tests.
5. **Copilot, boolean version in `ready`.** Same fix as item 3. The
   `incompatible_backend (bool)` case was added to the rejection table.

The protocol reference's ready-verification rule 3 and its exit-handling
guidance were updated, and the evidence record gained a PR review round
section.

# Validation

Run in the pinned session-scratch venv (Black 26.3.1, Ruff 0.15.12,
Python 3.11.8, macOS arm64):

- `scripts/format --check --diff`: 261 files unchanged. `scripts/lint`: exit 0.
- `scripts/test --log`: `Ran 1774 tests in 117.417s`, OK.
- `lrh validate`: 0 errors, 0 warnings.
- Desktop suites with `-W always::ResourceWarning`: 77 tests OK (43 protocol
  unit, 13 supervisor unit, 21 smoke). No resource warnings.

# Follow-up

Thread resolution is left to `/lrh-confirm-fixes`.
