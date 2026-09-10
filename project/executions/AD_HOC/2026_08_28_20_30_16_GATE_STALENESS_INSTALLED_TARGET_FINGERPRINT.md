---
execution_id: 2026_08_28_20_30_16_GATE_STALENESS_INSTALLED_TARGET_FINGERPRINT
prompt_id: PROMPT(AD_HOC:GATE_STALENESS_INSTALLED_TARGET_FINGERPRINT)[2026-08-28T18:13:51+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/648
commit: 7b5c8a409d67953435d9cda3cfb707ea603f8df0
created_at: 2026-08-28T20:30:16+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/512
session_transcript: claude-app:23a15fdd-6d6c-4d84-a7be-960a54769157
---

# Summary

Filed `WI-GATE-STALENESS-INSTALLED-TARGET-FINGERPRINT`, the work item to
fix `src/lrh/gate_staleness.py`'s installed-client-repo false negative —
the direct follow-up to the P1 finding left open on PR #512, which
survived investigation and remained unaddressed by the later
`WI-LRH-CHAIN-DEFAULTS-INCREMENT-3` staleness redesign.

# Result

Created `project/work_items/proposed/WI-GATE-STALENESS-INSTALLED-TARGET-FINGERPRINT.md`,
opened PR #648. Re-verified the finding's file:line citations
(`gate_staleness.py:34-45,186-208,221-224`) still held at the fresher
commit this worktree was created from (churn had continued in the
interim). Confirmed no duplicate work item via a fresh search;
`WI-CHAIN-DEFAULTS-STALENESS-RESTAMP` is unrelated (re-stamping, not
watch-path logic). Related to `WS-INVOCATION-AND-GATE-RESET` (the
active workstream owning `gate_staleness.py`), not the now-resolved
`WS-LRH-CHAIN-DEFAULTS`.

# Validation

- `lrh validate`: 0 errors, 0 warnings

# Follow-up

- Implementation itself is not started — this record covers filing
  only.
