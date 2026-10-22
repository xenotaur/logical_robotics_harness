---
execution_id: 2026_10_08_23_59_48_LRH_CONSOLE_MAP_STATIC_CLOSEOUT_NOTE
prompt_id: PROMPT(WI-LRH-CONSOLE-MAP-STATIC:LRH_CONSOLE_MAP_STATIC_CLOSEOUT_NOTE)[2026-10-08T23:59:48+00:00]
work_item: WI-LRH-CONSOLE-MAP-STATIC
status: landed
rerun_of: 2026_10_08_19_04_48_LRH_CONSOLE_MAP_STATIC
pr: https://github.com/xenotaur/logical_robotics_harness/pull/800
commit: 2f64eee46cabd6254943d8b8155489511a17a757
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/800"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-10-08T23:59:48+00:00
---


# Summary

This is the closeout note for PR #800, which implemented `WI-LRH-CONSOLE-MAP-STATIC` through
`/lrh-execute WS-LRH-CONSOLE-LOCAL-DOGFOOD`. The primary record's body is immutable, so the chain
note lives here instead.

# Result

CHAIN-NOTE: `cycles=1; stops=0; gates=[execute-chain, layout-decision, land-chain, owner-check, review-response, merge]; friction=owner-visual-feedback; self_review_rounds=2; bot_rounds=1; note="This added the first drawn dependency map, plus the Table and Blockers views, script-free in the frame. The owner approved a minimal LayeredGridLayout behind a swappable Layout interface, after an evaluation rejected networkx, grandalf, igraph, and graphviz. Browser checks caught clipped cards and a collapsed table, and a test caught ordering that would not settle. The pre-push review fixes were applied. The owner checked it in LRH Console, which the agent launched: it looked good overall, and their feedback was triaged. Fixed: readiness shown for closed items, cut-off titles, and Show on map. Filed: an outline layout and status shapes. All 4 bot threads were fixed: list-mode parity, unmet needs from edges, and HEAD matching GET. CI went 7/7 green, and the merge was SHA-locked."`

PR #800 merged as `2f64eee46cabd6254943d8b8155489511a17a757`, using
`--match-head-commit 58292ec7`, after authorization in this session. Three records landed with
that commit, through `lrh prompt update-execution`: the primary, `_REVIEW`, and `_CONFIRM`.

`WI-LRH-CONSOLE-MAP-STATIC` moved to `resolved/` with a resolution note.
`WS-LRH-CONSOLE-LOCAL-DOGFOOD` stays active.

# Validation

- `lrh validate` was run after these closeout edits. See the closeout commit.

# Follow-up

- These are now unblocked: `WI-LRH-CONSOLE-INTERACTIVE` (it also depends on THEME, which is
  resolved), `WI-LRH-CONSOLE-L1-DOGFOOD`, `WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT`, and
  `WI-LRH-CONSOLE-STATUS-SHAPES`.
- `WI-LRH-CONSOLE-STATUSBOARD` still needs the owner's band-set decision.
- Possible later work: cache snapshots by fingerprint, since each request takes about 0.8 s on
  the real view.
