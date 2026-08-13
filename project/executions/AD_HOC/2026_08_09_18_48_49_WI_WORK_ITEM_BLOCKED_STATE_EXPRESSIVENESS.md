---
execution_id: 2026_08_09_18_48_49_WI_WORK_ITEM_BLOCKED_STATE_EXPRESSIVENESS
prompt_id: PROMPT(AD_HOC:WI_WORK_ITEM_BLOCKED_STATE_EXPRESSIVENESS)[2026-08-09T18:47:01+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/535
commit: 98b128ed733a7b125a68f7d5d8db1308e6b62fd6
created_at: 2026-08-09T18:48:49+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-WORK-ITEM-BLOCKED-STATE-EXPRESSIVENESS.md
session_transcript: claude-app:3c4e404b-8420-4a62-9c3f-f5dcccfa5400
---

# Summary

Create `WI-WORK-ITEM-BLOCKED-STATE-EXPRESSIVENESS` for a control-plane gap found
while addressing finding #8 of an independent review: a `proposed` work item
cannot express that it must not be started, and readiness therefore reports it
as ready.

# Result

Created `project/work_items/proposed/WI-WORK-ITEM-BLOCKED-STATE-EXPRESSIVENESS.md`
(`type: deliverable`, `status: proposed`).

The gap is emergent from three individually-reasonable rules, each verified
against source rather than inferred:

1. `src/lrh/control/work_item_policy.py:139-147` — `blocked: true` raises
   `WORK_ITEM_BLOCKED_STATUS_INVALID` unless `status` is `active`.
2. `src/lrh/control/validator.py:1502-1509` — `blocked_by:` is validated against
   `set(work_item_map)` with `UNKNOWN_BLOCKER`, so it accepts only work-item IDs.
3. `src/lrh/assist/work_item_prompt_core.py:100-106` —
   `evaluate_prompt_readiness` adds "work item is marked blocked" only when that
   flag is set.

Together: a `proposed` item blocked by a non-work-item artifact has no valid
representation and reports `prompt_ready: yes`.

Discovered empirically rather than by inspection. Attempting to mark
`WI-LRH-CHAIN-DEFAULTS-INCREMENT-3` blocked produced
`WORK_ITEM_BLOCKED_STATUS_INVALID` from `lrh validate`; its actual blocker is
the DEC record from `WS-INVOCATION-AND-GATE-RESET` Stage 3, which `blocked_by:`
cannot reference. The constraint currently lives in a prose banner, which a
human reads and a chain runner does not — and `/lrh-execute` resolves "next
ready WI under a WS-ID", with `WS-LRH-CHAIN-DEFAULTS` owning that item.

The work item deliberately does not pre-commit to a fix. Three candidate
representations are listed (relax the status rule, add a non-work-item blocker
field, or introduce an `on_hold` status) with the choice left to design, since
both existing rules have defensible intent and the defect is in their
combination rather than in either alone.

**A self-correction worth recording, because it nearly went the wrong way.** A
prior project note recorded that `WorkItem.blocked` has three projection paths,
naming `validator.py` and `snapshot_cli.py` as bypassing the typed field. An
initial check for `src/lrh/cli/snapshot_cli.py` found nothing, and the Risk
Notes were first written to flag that note as stale.

That was wrong. The file is at `src/lrh/assist/snapshot_cli.py` — the search
looked in the wrong directory. Re-checked before the correction shipped, and the
note is accurate: `planning_tree.py:256` does recompute
`blocked=_frontmatter_bool(artifact.frontmatter, "blocked")`, and `snapshot_cli`
consumes that projection.

The corrected Risk Notes are consequently *stronger* than the original draft: at
least five sites read `blocked`, only one via the typed model. Had the
"stale note" version shipped, this work item would have understated its own
central risk while appearing to have verified it — the same failure mode as the
LCATS miscount corrected earlier in this session, and caught the same way, by
checking rather than asserting.

# Validation

- `lrh prompt check-execution --slug wi-work-item-blocked-state-expressiveness
  --work-item AD_HOC` → exit 0, no prior record.
- `lrh validate` → 0 errors, 1 warning (pre-existing, unrelated).
- `lrh work-items readiness WI-WORK-ITEM-BLOCKED-STATE-EXPRESSIVENESS` →
  `prompt_ready: yes`, confirming the `## Validation` section parsed as bullets.
- Prior-art search across `project/work_items/`,
  `project/design/proposals/proposed/`, and `project/design/backlog.md` found no
  existing artifact covering blocked-state expressiveness or readiness
  selection; keyword matches were incidental.

# Follow-up

No PR opened; the branch is pushed without one, so no automatic bot review fires.

`related_workstreams:` left empty. The gap was surfaced by
`PROP-INVOCATION-AND-GATE-RESET` but is not that program's scope, and no
existing workstream covers control-plane schema. Open to being adopted by one.

**Updated 2026-08-09:** brought into `WS-CROSS-REPO-CODE-HEALTH`'s scope later in the same session. Whether it is currently in that workstream's `work_items:` depends on sequencing — consult that field rather than this note, which is not kept in sync with it.

This work item is itself an instance of the problem it describes: it reports
`prompt_ready: yes` and has no blocker, which is correct — but it sits beside
`WI-LRH-CHAIN-DEFAULTS-INCREMENT-3`, which reports the same and should not.
Until this lands, that banner is the only guard.
