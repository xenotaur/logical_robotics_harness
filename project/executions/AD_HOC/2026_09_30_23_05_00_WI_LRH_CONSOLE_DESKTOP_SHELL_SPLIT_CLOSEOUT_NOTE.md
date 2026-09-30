---
execution_id: 2026_09_30_23_05_00_WI_LRH_CONSOLE_DESKTOP_SHELL_SPLIT_CLOSEOUT_NOTE
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_SHELL_SPLIT_CLOSEOUT_NOTE)[2026-09-30T23:05:00+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_09_30_22_00_03_WI_LRH_CONSOLE_DESKTOP_SHELL_SPLIT
pr: https://github.com/xenotaur/logical_robotics_harness/pull/760
commit: b9c1091250ed3fe5ad648b045b5fca89149f10d1
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/760"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-09-30T23:05:00+00:00
---

# Summary

Closeout note for PR #760, which split `WI-LRH-CONSOLE-DESKTOP-SHELL` at the
configuration/recovery boundary and added `WI-LRH-CONSOLE-DESKTOP-SETTINGS`.
The `/lrh-land` closeout wrote this note. The primary record's body is
immutable, so the chain note lives here.

# Result

CHAIN-NOTE: `cycles=1; stops=1; gates=[land-chain, ci-stop, review-response, confirm-fixes, merge]; friction=coverage-flake; self_review_rounds=1; bot_rounds=1; note="Codex and Copilot reviewed the first push and left 5 planning findings, all fixed in one round: ownership notes, mirrored acceptance lists, and mandatory serialization. Coverage failed once on a record-only commit, in an existing desktop_protocol_test that timed out at 10 s; the user treated it as a flake, and it passed on the next push. The substitute cold review found the PR safe, and its 2 low findings and 1 nit were fixed, including restoring the dropped workspace-mismatch gate. Merged with the SHA lock after 5/5 CI green."`

PR #760 merged as `b9c1091250ed3fe5ad648b045b5fca89149f10d1` with
`--match-head-commit b73e7d28`, after in-session merge authorization. Three
records landed with that commit: the primary, `_REVIEW`, and `_CONFIRM`.

No work item changed status at closeout. SHELL, SETTINGS, and DOGFOOD stay
`proposed`.

# Validation

- `lrh validate` was run after these closeout edits. See the closeout commit.

# Follow-up

- **Deferred nit:** the module comment in `apps/desktop/src-tauri/src/lib.rs`
  says Settings/Details and the recovery pages arrive with SHELL. Fix it when
  the SHELL implementation rewrites that file.
- **Coverage flake:**
  `tests/cli_tests/desktop_protocol_test.py::test_shutdown_stops_server_and_reports_lifecycle`
  hit its 10 s `_WAIT_SECONDS` once under coverage on ubuntu. If it recurs,
  file a work item for that test's timing.
- **Next:** `/lrh-execute WS-LRH-CONSOLE-LOCAL-DOGFOOD`, which should resolve to
  the narrowed `WI-LRH-CONSOLE-DESKTOP-SHELL`.
