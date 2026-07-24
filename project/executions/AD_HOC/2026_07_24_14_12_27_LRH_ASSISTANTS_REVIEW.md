---
execution_id: 2026_07_24_14_12_27_LRH_ASSISTANTS_REVIEW
prompt_id: PROMPT(AD_HOC:LRH_ASSISTANTS_REVIEW)[2026-07-24T14:07:24-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/414
commit: 
created_at: 2026-07-24T14:12:27-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/414
session_transcript: claude-app:local_9925d25c-1dab-4b64-bfa1-b484c2fa75fe
---

# Summary

Review-response round on PR #414 (design proposal `PROP-LRH-ASSISTANTS`).
Addressed three automated-reviewer comments (Copilot + Codex) against
`project/design/proposals/proposed/lrh-assistants/00_proposal.md`.

`rerun_of` is intentionally empty: the PR was created via `/lrh-proposal`,
which produces no primary execution record, so there is no originating record
to link. This review record is the first execution artifact for the branch.

# Result

All three comments were verified against the live codebase before acting;
all three were valid and fixed in-scope (no skips, no design-decision
conflicts).

1. **Prior-art accuracy (Copilot, `#discussion_r3647040193`).** The
   duplication-search bullet claimed every "assistant" grep hit resolved to
   `src/lrh/assist/`. Re-running the grep showed matches also in the
   `lrh-readiness` skill docs and three other proposals
   (`workstream-execution-framework`, `lrh-conversations-storage-interop`,
   `activity-lanes-and-observational-dashboard`). Corrected the bullet to list
   the real match locations and to state that none implement an assistant role
   artifact class.

2. **Binding grant, P1 (Codex, `#discussion_r3647043703`).** Decision 4's
   resolver intersects a `binding grant`, but Decision 5 defined no grant
   field, so a literal implementation would deny-all or over-authorize by
   treating the ceiling as the grant. Rewrote Decision 5 to define
   `assistant_contract` as the active grant that compiles to
   `AssistantBinding.granted_permissions`; the grant must be a subset of the
   `permission_ceiling` (binding validation rejects out-of-ceiling tokens), and
   a mutation-capable capability with no grant resolves as *unavailable* rather
   than falling back to the ceiling. (Consistent with the source design's
   `AssistantBinding.granted_permissions` field and its "granted permission
   outside the assistant ceiling" binding error.)

3. **Multi-parent inheritance, P2 (Codex, `#discussion_r3647043712`).**
   Verified that `src/lrh/control/planning_tree.py` emits
   `PLANNING_MULTIPLE_PARENTS` at severity `"warning"` (line ~561), so a child
   reachable from two differently-managed roots is a supported state, not an
   impossible edge. Clarified that inherited association is display/reporting
   only and never contributes to the grant (authority is resolved against the
   governing root binding of the subtree a run packet targets), and added a
   binding-validation rule that rejects a workstream reachable from two
   differently-managed roots so no child carries two grants or two reporting
   contracts.

# Validation

- `scripts/version tools` — Black 26.3.1, Ruff 0.15.12, Python 3.11.15 confirmed.
- `scripts/format --check --diff` — 179 files unchanged.
- `scripts/lint` — ruff + black all checks passed.
- `scripts/test` — full suite exit 0.
- `lrh validate` — 0 errors, 0 warnings.

Change is markdown-only (the proposal document); no Python was modified. The
format/lint/test sequence was run for evidence and passed cleanly.

Fixes pushed to the open PR branch: `03d9253..b9182c3`.

# Follow-up

- Run `/lrh-confirm-fixes` on PR #414 to verify the pushed fixes against the
  current diff and resolve the review threads before merge.
- After merge: set this record's `status: landed` and populate `commit:` with
  the merge SHA, then land it on `main` via closeout.
