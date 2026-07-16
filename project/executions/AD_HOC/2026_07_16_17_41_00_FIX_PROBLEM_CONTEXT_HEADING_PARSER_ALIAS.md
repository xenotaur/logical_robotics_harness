---
execution_id: 2026_07_16_17_41_00_FIX_PROBLEM_CONTEXT_HEADING_PARSER_ALIAS
prompt_id: PROMPT(AD_HOC:FIX_PROBLEM_CONTEXT_HEADING_PARSER_ALIAS)[2026-07-16T17:41:00-04:00]
work_item: AD_HOC
status: landed
rerun_of:
pr:
commit:
created_at: 2026-07-16T17:41:00-04:00
agent: claude_app
instruction_source: background task spawned from project/executions/AD_HOC/2026_07_16_15_58_09_WI_CONFIRM_FIXES_HEADING_FIX_REVIEW.md
session_transcript: pending
---

# Summary

Fixed the root-cause mismatch between `work-item-body-guide.md`'s documented
canonical heading `## Problem / Context` and
`work_item_prompt_core.parse_work_item_markdown()`'s exact-key lookup
`sections.get("problem", "")`, which silently left `parsed.problem` empty
for every work item following the documented convention. This is the
follow-up fix flagged in PR #395's review-response execution record
(`2026_07_16_15_58_09_WI_CONFIRM_FIXES_HEADING_FIX_REVIEW.md`), which
worked around the bug locally on one file (`WI-SKILLS-LRH-CONFIRM-FIXES.md`)
by renaming its heading to `## Problem`.

# Result

Chose Option 1 (fix the parser) over Option 2 (fix the docs), since it
preserves the more descriptive documented heading name and touches fewer
files:

- `src/lrh/assist/work_item_prompt_core.py`: `parse_work_item_markdown()`
  now resolves `problem` via
  `sections.get("problem", sections.get("problem / context", ""))`,
  mirroring the existing `out_of_scope`/`non-goals` alias-fallback pattern
  already used one line below in the same function.
- `tests/assist_tests/work_item_prompt_core_test.py`: added
  `test_parse_recognizes_problem_context_heading_alias`, asserting a work
  item using the exact canonical `## Problem / Context` heading from the
  body guide produces a non-empty `parsed.problem` that flows through to
  `build_work_item_prompt_data().objective`.

No documentation change was needed — `work-item-body-guide.md` already
documented the correct canonical heading; the parser was the thing out of
sync with it.

**Known-affected file check:** `WI-SKILLS-LRH-WORK-ITEM-COMPOSABLE.md` (in
`project/work_items/resolved/`, uses `## Problem / Context`) was confirmed
broken before this fix and confirmed fixed after, via direct parser calls
(see Validation). Its heading was left unchanged since it already matches
the documented convention.

A repo-wide grep for `## Problem / Context` across
`project/work_items/**/*.md` found only that one file plus the
already-locally-patched `WI-SKILLS-LRH-CONFIRM-FIXES.md` (which now reads
`## Problem`, from PR #395). No other files were affected.

# Validation

```
scripts/version tools  — lrh CLI present, Ruff 0.15.12, Black 26.3.1 (LRH conda env)
scripts/format --check --diff  — 179 files unchanged
scripts/lint  — All checks passed (ruff + black)
scripts/test  — full suite passed, exit 0 (including new/updated
  tests/assist_tests/work_item_prompt_core_test.py: 5 tests OK)
lrh validate  — 0 errors, 0 warnings
Direct parser verification against project/work_items/resolved/WI-SKILLS-LRH-WORK-ITEM-COMPOSABLE.md:
  parsed.problem non-empty: True (before fix: False)
  build_work_item_prompt_data().objective == parsed.problem: True (before fix: fell back to summary)
```

# Follow-up

- Update `session_transcript: pending` to the real session id after the
  session ends.
- No other files require heading or parser changes; the alias fallback
  covers all current and future work items using the documented
  `## Problem / Context` heading.
