---
execution_id: 2026_10_12_21_21_39_LRH_CONSOLE_MAP_FILTER_COLLAPSE_SELFREVIEW
prompt_id: PROMPT(AD_HOC:LRH_CONSOLE_MAP_FILTER_COLLAPSE_SELFREVIEW)[2026-10-12T21:21:39+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_10_12_21_21_39_LRH_CONSOLE_MAP_FILTER_COLLAPSE
pr: https://github.com/xenotaur/logical_robotics_harness/pull/835
commit: 4d4efd8751909bd8f6d53446ccbfc24b33771f22
created_at: 2026-10-12T21:21:39+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/835
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

This record covers a diff-mode `/lrh-self-review` of `WI-LRH-CONSOLE-MAP-FILTER-COLLAPSE` (commit `332c6c5a`), run before the PR's first push (PR #835). A cold-context `general-purpose` subagent did the review, report-only.

# Result

There were no High or Medium findings. The implementing session reproduced the top finding (offscreen table rows dropped without being counted) with a probe. It also reproduced the empty-view message. All five Low findings were fixed by that session in `a7a93550`. The skill was not run with `--apply`.

1. **Table:** the table dropped rows for items outside the view, while the note never counted them. Those rows now stay.
2. **Empty view:** with `?hide=`, an empty view said "The filters hide every item". It now shows the no-items message unless the filter actually removed a card.
3. **Test placement:** `FilterTest` sat below the `__main__` guard. It is moved above it.
4. **Empty rows:** under any filter, lanes and phases that were already empty also disappeared. Now only rows the filter emptied go.
5. **Narrow screens:** the scroll on load found map cards only. It now also finds the visible list entry. With scripts off there is still no scroll, which the PR records.

The review's test gaps are now covered: transitive needs, dropped lines, a fixture lifecycle that matches the state, offscreen table rows, the empty view, and rows that were empty before filtering.

# Validation

- `scripts/test`: all pass after the fixes.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- None. The PR still gets its first hosted bot review.
