---
execution_id: 2026_08_21_04_42_34_PARSER_COMMENT_IN_LIST
prompt_id: PROMPT(AD_HOC:PARSER_COMMENT_IN_LIST)[2026-08-21T04:42:34+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/574
commit: 83fe906a61b94f2dcea37efad0717141e0565d17
created_at: 2026-08-21T04:42:34+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/574
session_transcript: claude-app:cae5ad57-d961-4ce2-80b7-c25c28cb221c
---

# Summary

Backfill primary execution record for PR #574 (`xenotaur/fix/parser-comment-in-list`).

Fix two bugs in `lrh.control.parser._parse_frontmatter_mapping`'s inner
block-list accumulator loop:
1. An unindented comment (`# comment`) broke the inner loop early via `break`,
   causing silent data loss for any items that followed the comment.
2. An indented comment (`  # comment`) hit the `candidate.startswith("  ")`
   guard and raised `ValueError("unsupported nested mapping")`.

Added a three-line guard after the blank-line skip and before the
nested-mapping error:
```python
if stripped_candidate.startswith("#"):
    index += 1
    continue
```

Added 5 regression tests (all discriminating); fixed black formatting.

# Result

PR merged as commit `83fe906a`. All 5 CI checks green. Copilot clean pass on
first push. Substitute self-review round 1 surfaced a P3 non-discriminating
test; fixed. Substitute self-review round 2 clean.

CHAIN-NOTE: cycles=2; stops=0; gates=[merge]; friction=lint-failure; self_review_rounds=2; note="lint failed (black) on first push; fixed; self-review round 1 surfaced P3 non-discriminating test; test fixed; round 2 clean"

# Validation

- 1109 tests passed (`python -m pytest tests/ -q`)
- `lrh validate`: 0 errors, 0 warnings

# Follow-up

None.
