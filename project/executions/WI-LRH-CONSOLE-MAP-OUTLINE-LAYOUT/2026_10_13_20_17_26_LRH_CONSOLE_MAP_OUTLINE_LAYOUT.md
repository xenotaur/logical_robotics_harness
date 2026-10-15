---
execution_id: 2026_10_13_20_17_26_LRH_CONSOLE_MAP_OUTLINE_LAYOUT
prompt_id: PROMPT(WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT:LRH_CONSOLE_MAP_OUTLINE_LAYOUT)[2026-10-13T19:38:35+00:00]
work_item: WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/842
commit: 1ee5fefbee240e680aac50938b7d88c420d3b657
created_at: 2026-10-13T20:17:26+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/842
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

This record covers the implementation of `WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT` under `/lrh-execute`. The owner approved the run plan and both design recommendations: ordering within each lane, and phase rows still constraining the order. The default layout is decided after the owner compares both layouts.

# Result

This section describes the implementation round. Review then made the outline the default (the toggle now reads Outline · Grid), kept indented cards full width, and refined the cycle break. See the `_REVIEW` and `_CONFIRM` records.


- **`layout.py`:**
  - `OutlineLayout` lists each lane-and-phase cell's cards in dependency order, with a dependent just under what it needs.
  - It indents cards by depth within the cell: 24 px per level, capped at 4 levels.
  - Lines inside a cell run down a left rail. Lines between cells use the grid's routes, computed from the column edge, so they stay clear of indented cards.
  - Cycles are broken one card at a time.
  - `LAYOUTS` and `layout_named` choose a layout by name, falling back to the default.
- **`render.py`:** `_Links` carries `layout`, so every in-page link keeps it. A Layout toggle (Grid · Outline) sits beside the filters and is hidden on narrow screens.
- **`serve.py`:** reads `?layout=`.
- **Script:** `syncLinks` covers the toggle links.
- **Docs:** `serve.md` documents `?layout=`.
- **Browser check:** on LCATS `worldcon-2026` with Done hidden, the EVENT and SF chains render as stepped outlines. The LRH view keeps its six phase rows.
- **Pre-push self-review:** 1 Medium and 3 Low findings, all fixed. See the `AD_HOC` `_SELFREVIEW` record.
- **Pending:** the owner's side-by-side comparison and the default-layout decision.

# Validation

- `scripts/format --check --diff`: clean.
- `scripts/lint`: clean.
- `scripts/test`: 2327 tests, OK.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- Record the owner's default-layout decision in the PR and in the visual-language proposal, then land through `/lrh-land`.
