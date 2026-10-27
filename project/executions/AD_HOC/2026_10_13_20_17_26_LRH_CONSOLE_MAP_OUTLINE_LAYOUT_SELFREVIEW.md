---
execution_id: 2026_10_13_20_17_26_LRH_CONSOLE_MAP_OUTLINE_LAYOUT_SELFREVIEW
prompt_id: PROMPT(AD_HOC:LRH_CONSOLE_MAP_OUTLINE_LAYOUT_SELFREVIEW)[2026-10-13T20:17:26+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_10_13_20_17_26_LRH_CONSOLE_MAP_OUTLINE_LAYOUT
pr: https://github.com/xenotaur/logical_robotics_harness/pull/842
commit: 1ee5fefbee240e680aac50938b7d88c420d3b657
created_at: 2026-10-13T20:17:26+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/842
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

This record covers a diff-mode `/lrh-self-review` of `WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT` (commit `f4cf30f1`), run before the PR's first push (PR #842). A cold-context `general-purpose` subagent did the review, report-only. It used probe scripts in the scratchpad: a line-versus-card crossing checker, an in-cell order checker and a determinism check.

# Result

The implementing session reproduced the Medium finding with the reviewer's probe. It fixed all findings in its own draft before the push, without `--apply`.

1. **Medium:** lines between cells crossed less-indented cards. `_orthogonal` placed left-side gutters relative to the card's left edge, which moved inside the column once the indent reached two or more levels. Routes are now computed from the column edge, and the end steps are extended along the card's own row. The probe now finds no crossings, and a test checks it.
2. **Low:** the cycle fallback placed every remaining card in ID order, which could misorder edges outside the cycle. It now breaks one card at a time, and a test covers this.
3. **Low:** test gaps. There are new tests for crossings, cycle order, and the cycle diagnostic on an outline page.
4. **Low:** the toggle appeared after the diagnostics, and also on narrow screens where the list ignores layout. It now sits beside the filters and is hidden on narrow screens.

The review also confirmed:

- the outline order is a valid topological order (0 in-cell violations on the real LRH view, against 5 for the grid);
- the grid's output is unchanged;
- every link keeps `layout`;
- the output is deterministic.

# Validation

- `scripts/test`: 2327 tests, OK, after the fixes.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- None. The PR still gets its first hosted bot review.
