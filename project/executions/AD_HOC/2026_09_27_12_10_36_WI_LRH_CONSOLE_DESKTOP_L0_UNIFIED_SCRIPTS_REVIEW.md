---
execution_id: 2026_09_27_12_10_36_WI_LRH_CONSOLE_DESKTOP_L0_UNIFIED_SCRIPTS_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_L0_UNIFIED_SCRIPTS_REVIEW)[2026-09-27T12:09:44+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_09_27_03_58_19_WI_LRH_CONSOLE_DESKTOP_L0_UNIFIED_SCRIPTS_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/744
commit: 
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/744"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-09-27T12:10:36+00:00
---

# Summary

Review-response round 2 for PR #744. The confirm-fixes Step 8 substitute cold
review on HEAD `e9b3a880` judged the PR safe to merge and reported four
low-severity items. The user chose to fix all four before the merge gate.
This is a same-run continuation of the round-1 `_REVIEW` record.

# Result

All four were fixed in `b1db7a22`:

1. **Desktop CI missed backend changes.** The `desktop.yml` triggers now
   include `src/lrh/desktop_protocol.py`, `src/lrh/desktop_supervisor.py`,
   and `src/lrh/serve.py`, so a backend protocol change runs the tier-1
   integration tests in the same PR.
2. **SKIPPED line implied a toolchain probe.** The default line is now
   `desktop: SKIPPED (not requested; run scripts/test --desktop)`. It is
   always printed and never depends on probing cargo or rustup.
3. **Duplicate validation bullets.** The two `desktop_modes_test.py` bullets
   were merged into one.
4. **`--install-rust` silently ignored without `--desktop`.** That
   combination is now rejected with a usage error and a non-zero exit, and
   the case is added to `desktop_modes_test.py`.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items readiness WI-LRH-CONSOLE-DESKTOP-L0`: `prompt_ready: yes`,
  no warnings.

The change is planning text only.

# Follow-up

Confirm-fixes and the REVIEW-LANDED check on the new HEAD follow.
