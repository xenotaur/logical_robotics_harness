---
execution_id: 2026_07_31_17_00_41_WI_LRH_ASSISTANTS_STAGE_2_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_ASSISTANTS_STAGE_2_REVIEW)[2026-07-31T16:59:35-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/448
commit: c95e74c
created_at: 2026-07-31T17:00:41-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/448
session_transcript: claude-app:9925d25c-1dab-4b64-bfa1-b484c2fa75fe
---

# Summary

Review-response round on PR #448 (file WI-LRH-ASSISTANTS-STAGE-2 blocked +
amend WS-LRH-ASSISTANTS gate), run via `/lrh-land`. No primary execution
record exists for this PR (backfill path); this is the only execution record
until the closeout backfill record is authored in Step 7.

# Result

Addressed three automated-reviewer comments (Copilot x1, Codex x2). All three
were verified against source before acting; one contained a factually
incorrect premise that was corrected rather than accepted.

1. **Copilot — depends_on scope wording.** The blocked_reason claimed
   `lrh validate` resolves `depends_on` only against work items "that exist on
   main." Verified (`src/lrh/control/validator.py`'s `_validate_relation_field`
   against `work_item_map`): the real constraint is the project tree being
   validated, not specifically main -- a WI added in the same branch resolves
   fine. Reworded to state the accurate mechanism and clarify the practical
   point still holds (the dependency's WIs don't exist anywhere yet).
2. **Codex P2 -- blocked flag invisible to `lrh serve`.** Verified precisely:
   `core_state.py`'s `WorkItemState`/`_work_item_states()` drop `blocked`/
   `blocked_reason`, and `serve.py`'s `_blocked_work_item_count()` only counts
   `blocked_by`-non-empty or `status in {blocked, stalled}` -- never this WI's
   exact shape (`status: active`, `blocked: true`, `blocked_by: []`). Scoped
   the WI's "visible, honest leaf" claim to `lrh validate` specifically, and
   added a "Known gap" note. The actual core_state.py/serve.py fix is out of
   scope for this planning-only PR; flagged via spawn_task as a follow-up
   (task_872edf67) rather than folded in.
3. **Codex P2 -- assistant_role runtime target ambiguous.** Codex claimed no
   typed execution-record model/loader exists. Verified this premise is
   **false**: `ExecutionRecord` / `parse_execution_record()` exist in
   `src/lrh/prompt_workflow_records.py`. The underlying ambiguity was still
   real, though: none of the three already-documented optional fields
   (`agent`/`instruction_source`/`session_transcript`) are named dataclass
   attributes either -- all three are read via the catch-all `.frontmatter`
   dict. Resolved by naming the concrete target: `assistant_role` follows the
   same established pattern (no new dataclass field; read via
   `ExecutionRecord.frontmatter`), corrected in the WI text and acceptance
   criteria.

Fixes pushed to the open PR branch: `73bac14..baa9bdc`.

# Validation

- `lrh validate` -- 0 errors, 0 warnings.
- `lrh work-items validate` -- 0 errors (6 pre-existing unrelated warnings).
- `scripts/format --check` and `scripts/lint` -- clean.
- Change is markdown only (one file); no Python modified.

# Follow-up

- `/lrh-confirm-fixes` (inlined per `/lrh-land`) verifies these fixes against
  the diff and resolves the review threads before the merge gate.
- Follow-up task flagged (not part of this PR): project `blocked`/
  `blocked_reason` through `WorkItemState` and the `lrh serve` dashboard
  payload (task_872edf67).
