---
execution_id: 2026_09_30_22_37_41_WI_LRH_CONSOLE_DESKTOP_SHELL_SPLIT_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_SHELL_SPLIT_REVIEW)[2026-09-30T22:37:41+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/760
commit: 
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/760"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-09-30T22:37:41+00:00
---

# Summary

Review-response round 1 for PR #760, the SHELL split. It ran within
`/lrh-land`.

The `coverage` check failed on `ea3d8777`, a commit that only changed a
record. The failing test was the existing
`desktop_protocol_test.test_shutdown_stops_server_and_reports_lifecycle`, which
raised `queue.Empty` after its 10 s wait. The same code had passed coverage on
`598955a8`, and the PR contains no code, so it looks like a timing flake. The
failure fired the stop-work condition.

The hosted reviews left 5 inline threads: 1 from Codex and 4 from Copilot. The
user chose "Fix all 5, treat flake".

# Result

All five are fixed in `f0bc7287`:

1. **Stale ownership in resolved items** (Codex and Copilot, duplicate
   threads).
   - `WI-LRH-CONSOLE-DESKTOP-L0`'s Scope split now has a superseding note.
     SHELL owns windows, lifecycle menus, navigation and capability limits,
     and the capability test. SETTINGS owns Settings/Details, configuration,
     recovery pages, browser handoff, and the dogfood how-to.
   - `WI-LRH-CONSOLE-DESKTOP-SUPERVISOR`'s Summary and Non-Goals name
     SETTINGS for settings, recovery, and browser handoff.
2. **Body acceptance criteria dropped frontmatter gates** (Copilot, SHELL and
   SETTINGS). `work_item_prompt_core` prefers the body section, so the gates
   were being lost. Both body sections now mirror the frontmatter
   `acceptance` lists verbatim.
3. **Serialization was optional** (Copilot, SHELL). Serializing menu actions
   is now required. The item no longer allows documenting the two PR #758
   Start edge cases instead. The frontmatter acceptance now states it too.

The coverage failure is treated as a flake, as the user chose. The push re-runs
coverage. If it fails again, a follow-up work item will cover the test's
timing, rather than widening this planning PR.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items readiness`: `prompt_ready: yes`, with no warnings, for
  SHELL and SETTINGS.

# Follow-up

Next: confirm-fixes, which resolves the 5 threads, runs a substitute cold
review, and re-checks CI.
