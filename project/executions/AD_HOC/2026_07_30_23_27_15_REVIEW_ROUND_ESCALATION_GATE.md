---
execution_id: 2026_07_30_23_27_15_REVIEW_ROUND_ESCALATION_GATE
prompt_id: PROMPT(AD_HOC:REVIEW_ROUND_ESCALATION_GATE)[2026-07-30T23:21:17-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/444
commit: b6935b5eb291c874e26dd0ad0ab1e0b2cb1a1bd4
created_at: 2026-07-30T23:27:15-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-REVIEW-ROUND-ESCALATION-GATE.md
session_transcript: claude-app:b1f7a963-e611-4bcd-9d8c-a6a80d633a47
---

# Summary

Create the LRH work item `WI-REVIEW-ROUND-ESCALATION-GATE`, capturing the
design (via `/lrh-design`) for a durable, human-gated round-cap check on
the assist-model review/fix loop (`/lrh-review-response` ×
`/lrh-confirm-fixes`). This follows a multi-turn conversation analyzing
GitHub Copilot/Claude credit consumption from recent long review cycles
(PR #438, #442) and refining the mechanism from a single soft/hard round
cap into a recurring, escalating human gate (3 → 10 → 20 → ...), explicitly
scoped to the assist-model loop only (not aggregate Copilot spend, not
Jules- or human-originated PR activity, both of which are structurally
outside this mechanism's reach).

# Result

Ran `/lrh-design` first, which surfaced `WI-BOUNDED-STABILIZATION-LOOP-DESIGN`
as overlapping prior art (broader scope: CI-round limits, an autonomous
"bounded-auto" mode, blocked on three unresolved WIs) and paused for an
explicit user decision on how to relate the two; the user chose to proceed
standalone, cross-linked rather than folding in. Then ran `/lrh-work-item`
to capture the resulting design as `WI-REVIEW-ROUND-ESCALATION-GATE`
(`project/work_items/proposed/WI-REVIEW-ROUND-ESCALATION-GATE.md`),
including a recorded duplication/demand search verdict in `## Problem /
Context`, `related_workstreams: [WS-EXECUTION-FRAMEWORK]` as a
cross-reference only (not added to that workstream's `work_items:`
ownership list, so this item stays unblocked), and `forbidden_actions`
guarding against scope creep into the broader WI's territory
(`implement_ci_round_limits`, `implement_bounded_auto_mode`). Opened
[PR #444](https://github.com/xenotaur/logical_robotics_harness/pull/444)
from branch `xenotaur/feat/wi-review-round-escalation-gate`.

# Validation

- `lrh validate`: 0 errors, 1 pre-existing warning unrelated to this change
  (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on `WS-LRH-ASSISTANTS`).
- `lrh work-items validate`: 0 errors, 1 warning on this file
  (`unresolved-metadata-reference` for a `related_design` path under
  `project/memory/decisions/`) — matches an existing, accepted pattern on
  other resolved work items in this repo (`related_design` only resolves
  under `project/design/`), not a new problem introduced here.

# Follow-up

- This is a planning-only record; implementation (the actual skill/reference
  edits) happens under `/lrh-implement` when the work item is later
  executed, producing its own execution record.
- The user was offered a `WS-EXECUTION-FRAMEWORK` workstream-list update at
  the `/lrh-work-item` skill's Step 11 offer and had not yet responded as of
  this record; if declined or not taken up, no further action needed.
- `session_transcript: pending` should be updated once resolvable per
  established convention.
