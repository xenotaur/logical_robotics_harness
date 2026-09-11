---
execution_id: 2026_09_11_07_54_55_FIX_COUNT_TURNS_TOOL_RESULT
prompt_id: PROMPT(AD_HOC:FIX_COUNT_TURNS_TOOL_RESULT)[2026-09-11T07:54:16+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/665
commit: afd247e5
created_at: 2026-09-11T07:54:55+00:00
agent: claude_app
instruction_source: "ad-hoc task -- fix _count_turns() overcounting tool_result-only user records as human turns, per finding surfaced in WI-CLAUDE-CONVERSATION-EXPORT-API's PR #664 self-review"
session_transcript: pending
---

# Summary

Fixed `_count_turns()` in `src/lrh/conversations/claude_export.py`, which
counted every JSONL step with `type=="user"` and a `message` key as a
conversational turn. In the real Claude Code transcript format, a
`tool_result` reply is also delivered as a `type:"user"` record whose
`message.content` is a list containing a `{"type": "tool_result", ...}`
block, not human-typed text -- so `turn_count` overcounted real human
turns whenever a session included tool calls.

# Prior art

Found and independently re-verified during the substitute self-review
pass in WI-CLAUDE-CONVERSATION-EXPORT-API's PR #664
(https://github.com/xenotaur/logical_robotics_harness/pull/664), which
merged with the counting logic as originally specified in the work item
since it was judged cosmetic/statistics-only with no control-flow impact,
not a merge blocker. That PR's self-review record
(`project/executions/AD_HOC/2026_09_11_06_01_37_WI_CLAUDE_EXPORT_BATCH_SELFREVIEW.md`)
is the origin of this follow-up. No other in-repo or external duplicate of
this fix exists; no other open work item requests it.

# Result

- Added `_is_genuine_human_turn()` helper: returns True for a plain-string
  `message.content`, or a list containing at least one block that is not
  a `{"type": "tool_result"}` block; False otherwise.
- `_count_turns()` now requires `_is_genuine_human_turn(step)` in addition
  to the prior `type == "user"` and `"message" in step` checks.
- Added `_tool_result_user_record()` test helper and
  `test_turn_count_excludes_tool_result_only_user_records` in
  `tests/conversations_tests/claude_export_test.py`, covering a transcript
  that mixes tool_result-only user records with genuine human turns and
  asserts `turn_count` reflects only the human ones.
- Updated `test_convert_claude_session_renders_tool_use_and_tool_result` to
  assert `turn_count == 0` (its transcript has only a tool_result user
  record, no genuine human turn).

# Validation

- `PYTHONPATH=src python -m unittest tests.conversations_tests.claude_export_test -v`
  -- 26 tests, all pass.
- `scripts/format --check --diff` -- clean after `scripts/format`.
- `scripts/lint` -- ruff, black, and test-framework guardrails all pass
  (guardrails check required `PYTHONPATH=src`; this worktree's editable
  install points at a different checkout).
- `scripts/test` -- 1579 tests, all pass.
- `lrh validate` -- 0 errors, 2 pre-existing warnings unrelated to this
  change.
- `/lrh-self-review` diff-mode: cold-context subagent pass found no
  issues; top finding (diff satisfies stated requirements) independently
  re-verified directly by evaluating `_count_turns()` against a
  hand-built mixed transcript.

# Follow-up

None.
