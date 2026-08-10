---
execution_id: 2026_08_09_18_02_13_WI_LRH_CHAIN_DEFAULTS_INCREMENT_3
prompt_id: PROMPT(AD_HOC:WI_LRH_CHAIN_DEFAULTS_INCREMENT_3)[2026-08-09T18:00:34+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/535
commit: 98b128ed733a7b125a68f7d5d8db1308e6b62fd6
created_at: 2026-08-09T18:02:13+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-CHAIN-DEFAULTS-INCREMENT-3.md
session_transcript: claude-app:3c4e404b-8420-4a62-9c3f-f5dcccfa5400
---

# Summary

Create `WI-LRH-CHAIN-DEFAULTS-INCREMENT-3` under the existing
`WS-LRH-CHAIN-DEFAULTS`, covering the two chain-defaults defects that
`PROP-INVOCATION-AND-GATE-RESET` identified but does not own: the
`closeout_with_merge` single-ask field and the semantic staleness watch.

# Result

Created `project/work_items/proposed/WI-LRH-CHAIN-DEFAULTS-INCREMENT-3.md`
(`type: deliverable`, `status: proposed`, `depends_on:
WI-LRH-CHAIN-DEFAULTS-INCREMENT-1`).

Also updated `WS-LRH-CHAIN-DEFAULTS` to take ownership: added the new ID to its
`work_items:` list and an Increment 3 entry to its `exit_criteria:`. Ownership
lives in the workstream's `work_items:` field, so declaring
`related_workstreams:` on the work item alone would have left it related but
unowned — the same gap this session found on
`WI-DELIBERATE-MODEL-INVOCATION`.

Scope covers two defects, both documented in `PROP-INVOCATION-AND-GATE-RESET`:

- **Defect 1 — merge and closeout are one question asked twice.**
  `/lrh-land` Step 6 takes a live merge authorization; Step 7 inlines
  `/lrh-closeout`, whose Step 4 gate takes a second. The profile's own
  steelmanned completion condition defines done as a single unit ("PR merged,
  its execution records landed, and any linked work item resolved"), and Step 7
  is unconditional, so a merged-but-unclosed chain is unfinished rather than
  awaiting a fresh decision.
- **Defect 2 — the staleness watch is wrong in both directions.** File-granular,
  so a typo invalidates consent like a gate redesign; and it omits the three
  gate-bearing skills `/lrh-land` inlines (`/lrh-confirm-fixes`,
  `/lrh-review-response`, `/lrh-closeout`), so a real gate change there does not
  invalidate consent at all.

The work item records a dependency the implementation must respect: narrowing
`PROP-LRH-CHAIN-DEFAULTS` Decision 3 requires the DEC record from
`WS-INVOCATION-AND-GATE-RESET` Stage 3. Shipping `closeout_with_merge` before
that record lands would leave the codebase contradicting its own governing
document.

Written directly against the validated work-item pattern established earlier in
this session rather than by reloading `/lrh-work-item` — a deliberate choice
given the session's own subject matter, with the skill's substantive checks
(existence, slug idempotence, prompt ID, schema, readiness parse) all still
performed.

# Validation

- `lrh prompt check-execution --slug wi-lrh-chain-defaults-increment-3
  --work-item AD_HOC` → exit 0, no prior record.
- `lrh validate` → 0 errors, 1 warning (pre-existing, unrelated).
- `lrh work-items readiness WI-LRH-CHAIN-DEFAULTS-INCREMENT-3` →
  `prompt_ready: yes`, confirming the `## Validation` section parsed as bullets
  rather than a fenced block.
- Ownership verified before editing: `WS-LRH-CHAIN-DEFAULTS`'s `work_items:`
  previously listed three items and now lists four.

# Follow-up

No PR opened; the branch is pushed without one, so no automatic bot review is
triggered.

This work item is blocked in practice, though not marked `blocked:` — it depends
on `WI-LRH-CHAIN-DEFAULTS-INCREMENT-1` (already resolved) and on the Stage 3 DEC
record, which does not exist yet. The DEC dependency is recorded in Risk Notes
rather than in `blocked_by:`, since that field takes work-item IDs and the
blocking artifact is a decision record.
