---
execution_id: 2026_08_01_12_33_40_STRANGE_GREIDER_BF91AD_REVIEW
prompt_id: PROMPT(AD_HOC:STRANGE_GREIDER_BF91AD_REVIEW)[2026-08-01T12:26:19-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/455
commit: 3eed92d
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/455
session_transcript: pending
created_at: 2026-08-01T12:33:40-04:00
---

# Summary

Address Codex's open review comment on PR #455 (`fix(core-state): project
blocked/blocked_reason through to dashboard`): a P2 finding that
`blocked_reason` was only validated as a string when `blocked: true`,
leaving the strict loader's `_optional_str` free to raise `ValueError` on
a non-string `blocked_reason` (e.g. `123`) when `blocked` is `false`.

# Result

Extended `validate_work_item_policy()` in `src/lrh/control/work_item_policy.py`
so a non-null, non-string `blocked_reason` is reported as
`WORK_ITEM_BLOCKED_REASON_NOT_STRING` in the `blocked is not True` branch
(the `blocked is True` branch already covers non-string values via the
existing `WORK_ITEM_BLOCKED_REASON_REQUIRED` check, so this avoids a
duplicate error for that case). Added
`test_non_string_blocked_reason_is_error_when_not_blocked` to
`tests/control_tests/work_item_policy_test.py` covering
`status: active`, `blocked: false`, `blocked_reason: 123`.

Copilot's review on this PR left only a general (non-inline) comment; no
further actionable findings from that review.

# Validation

- `scripts/format --check --diff` — clean (179 files unchanged)
- `scripts/lint` — ruff + black, all checks passed
- `scripts/test` — 813 tests passed
- `lrh validate` — 0 errors, 1 pre-existing unrelated warning
  (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on `WS-LRH-ASSISTANTS`)

# Follow-up

None.
