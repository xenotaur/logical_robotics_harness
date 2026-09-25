---
execution_id: 2026_09_23_17_59_12_WI_CLAUDE_EXPORT_MARKDOWN_USER_TURN_MISLABEL
prompt_id: PROMPT(WI-CLAUDE-EXPORT-MARKDOWN-USER-TURN-MISLABEL:WI_CLAUDE_EXPORT_MARKDOWN_USER_TURN_MISLABEL)[2026-09-23T17:48:40+00:00]
work_item: WI-CLAUDE-EXPORT-MARKDOWN-USER-TURN-MISLABEL
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/717
commit: c45420dce5431b5f5425ab2ea5eab7d0cd13eee1
created_at: 2026-09-23T17:59:12+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-CLAUDE-EXPORT-MARKDOWN-USER-TURN-MISLABEL.md
session_transcript: claude-app:3278dd49-9852-4955-b978-00367552dc27
---

# Summary

Implemented `WI-CLAUDE-EXPORT-MARKDOWN-USER-TURN-MISLABEL` via `/lrh-execute`:
the `## User` render call site in `_render_claude_transcript()`
(`claude_export.py`) now checks `_is_genuine_human_turn(step)`, the same
helper `_count_turns()` already used, so a tool-execution-result reply no
longer renders under an identical `## User` heading to a genuine
human-typed message.

# Result

Edited `src/lrh/conversations/claude_export.py`:
- The `type=="user"` branch (line 667) now checks
  `_is_genuine_human_turn(step)` before rendering. A genuine turn still
  renders `## User` unchanged, via the existing `_render_message_block`.
- A tool-result-only turn now renders via a new `_render_tool_result_turn()`
  helper — deliberately no `##`-level wrapper heading, since each
  `tool_result` block already gets its own `### Tool Result` (or
  `### Tool Result (error)`) heading from the existing
  `_render_content_blocks`; adding a wrapper would have produced a
  redundant double heading for the common single-block case.
- The recursive subagent-transcript-inlining path
  (`_render_claude_transcript` calling itself) shares the same function
  body, so it inherits the fix with no separate code path — verified by a
  dedicated test, not just assumed.

Edited `tests/conversations_tests/claude_export_test.py`: 4 new tests —
the core fix (`test_tool_result_only_user_record_does_not_render_as_user_section`),
the subagent-recursion case
(`test_tool_result_distinction_applies_to_inlined_subagent_transcript`),
a mixed `tool_result`+`text` list that must still render as a genuine turn
(`test_mixed_tool_result_and_text_list_still_renders_as_user_section`,
proving `_is_genuine_human_turn`'s `any()` branch is respected), and
empty-content/missing-`message` edge cases
(`test_empty_content_and_missing_message_user_records_render_nothing`).

Manually rendered a sample 4-step transcript (genuine user turn → tool_use
→ tool_result → assistant text) end to end and inspected the output
directly: exactly one `## User` section, the tool result rendered as a
standalone `### Tool Result` block between the two `## Assistant`
sections, `turn_count` still correctly `1`.

**Diff-mode `/lrh-self-review` pass** (cold subagent, before first push):
verified the fix's correctness against `_is_genuine_human_turn()`'s actual
branches (genuine string/list content, tool-result-only, mixed list, empty
content, missing `message` key), confirmed the recursive subagent path
genuinely shares the fix by reading the call graph directly, confirmed
`_render_tool_result_turn`'s docstring claim about `_render_content_blocks`
always emitting its own `### Tool Result` heading, and confirmed diff
scope was exactly the two expected files. One nit (missing edge-case
tests for the empty-content/no-message and mixed-list cases) —
independently re-verified as a real, if minor, gap and fixed before this
push (the two additional tests above). No blocking or should-fix findings.

Scope held exactly to the WI: `turn_count`/`message_count` in
`export_manifest.py` untouched (unaffected by the bug, confirmed again
during implementation); no doc under `docs/` describes the header shape
(re-checked per Required Change 4, still true); sibling exporters
(Codex, Antigravity) untouched.

Opened https://github.com/xenotaur/logical_robotics_harness/pull/717.

**Branch-naming note:** `xenotaur/feat/wi-claude-export-markdown-user-turn-mislabel`
was already used by PR #715 (the planning PR). Its tip (`a070bc2d`) was
confirmed a genuine ancestor of `origin/main` before reset — safely reset
via `git checkout -B` from fresh `origin/main` rather than treated as a
fresh branch name.

# Validation

- `scripts/version tools` — ruff 0.15.12, black 26.3.1, versions as
  pinned.
- `PYTHONPATH=src scripts/format --check --diff` — clean.
- `PYTHONPATH=src scripts/lint` — clean.
- `PYTHONPATH=src python -m unittest tests.conversations_tests.claude_export_test -v` —
  53 tests OK (was 51, +2 edge-case tests added after the self-review nit).
- `PYTHONPATH=src scripts/test` — full suite + smoke, exit 0.
- `lrh validate` — 0 errors, 0 warnings.

# Follow-up

- Proceed to `/lrh-land` for PR #717.
