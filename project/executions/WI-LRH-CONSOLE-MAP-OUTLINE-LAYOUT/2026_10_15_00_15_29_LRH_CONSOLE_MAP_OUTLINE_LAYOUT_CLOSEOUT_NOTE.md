---
execution_id: 2026_10_15_00_15_29_LRH_CONSOLE_MAP_OUTLINE_LAYOUT_CLOSEOUT_NOTE
prompt_id: PROMPT(WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT:LRH_CONSOLE_MAP_OUTLINE_LAYOUT_CLOSEOUT_NOTE)[2026-10-15T00:15:29+00:00]
work_item: WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT
status: landed
rerun_of: 2026_10_13_20_17_26_LRH_CONSOLE_MAP_OUTLINE_LAYOUT
pr: https://github.com/xenotaur/logical_robotics_harness/pull/842
commit: 1ee5fefbee240e680aac50938b7d88c420d3b657
created_at: 2026-10-15T00:15:29+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/842
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

This is the closeout note for PR #842, which implemented `WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT` through
`/lrh-execute MAP-OUTLINE-LAYOUT`. The primary record's body is immutable, so the chain note lives here
instead.

# Result

CHAIN-NOTE: `cycles=1; stops=1; gates=[execute-chain, land-chain, review-response, owner-comparison, split-and-default, confirm-fixes-stop, stop-amended-continue, recheck, merge]; friction=cycle-break-took-three-tries; self_review_rounds=4; bot_rounds=1; note="This added an outline layout for dependency maps, and the owner made it the default after comparing both layouts on LRH and LCATS. Each lane-and-phase cell lists its cards in dependency order and indents them by depth, capped at four levels. Cards keep full width and lanes widen instead. Lines inside a cell run down a left rail, and lines between cells route from the column edge, so nothing crosses a card. A Layout toggle beside the filters and ?layout=layered-grid keep the grid one click away, and the grid's output is unchanged. The pre-push review caught lines crossing indented cards. Copilot and Codex caught a cycle break placed outside the cycle; the first fix was still partial when one cycle depended on another, which fired the stop condition. The owner chose option A, and a sink-cycle break fixed it (400-map and 20,000-graph fuzz tests, 0 failures). The owner's comparison led to full-width cards, the outline default, and WI-LRH-CONSOLE-MAP-EDGE-READABILITY for line drawing, plus the zoom and restart-shortcut items filed here. CI passed, and the merge was SHA-locked."`

PR #842 merged as `1ee5fefbee240e680aac50938b7d88c420d3b657`, using
`--match-head-commit 77e2d620`, after authorization in this session. Four records landed with that
commit, through `lrh prompt update-execution`: the primary, `_REVIEW`, `_CONFIRM`, and the pre-push
`AD_HOC` `_SELFREVIEW`.

`WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT` moved to `resolved/` with a resolution note. At the owner's request,
`WI-LRH-CONSOLE-DESKTOP-ZOOM` and `WI-LRH-CONSOLE-DESKTOP-RESTART-SHORTCUT` were filed.
`WS-LRH-CONSOLE-LOCAL-DOGFOOD` stays active.

# Validation

- `lrh validate` was run after these closeout edits. See the closeout commit.

# Follow-up

- `WI-LRH-CONSOLE-MAP-EDGE-READABILITY`: a design discussion with the owner about how lines are drawn.
- `WI-LRH-CONSOLE-DESKTOP-ZOOM` and `WI-LRH-CONSOLE-DESKTOP-RESTART-SHORTCUT`: small desktop items.
