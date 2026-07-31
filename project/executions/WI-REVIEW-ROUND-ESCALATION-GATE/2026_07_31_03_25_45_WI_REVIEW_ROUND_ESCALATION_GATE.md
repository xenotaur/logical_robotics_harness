---
execution_id: 2026_07_31_03_25_45_WI_REVIEW_ROUND_ESCALATION_GATE
prompt_id: PROMPT(WI-REVIEW-ROUND-ESCALATION-GATE:WI_REVIEW_ROUND_ESCALATION_GATE)[2026-07-31T03:10:44-04:00]
work_item: WI-REVIEW-ROUND-ESCALATION-GATE
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/445
commit: 
created_at: 2026-07-31T03:25:45-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-REVIEW-ROUND-ESCALATION-GATE.md
session_transcript: pending
---

# Summary

Implement `WI-REVIEW-ROUND-ESCALATION-GATE`: add a durable, human-gated
round-cap check to `/lrh-confirm-fixes` Step 8's bot-retrigger loop.

# Result

Added the round-cap check to `src/lrh/skills/lrh-confirm-fixes/SKILL.md`
Step 8, inserted immediately before the existing retrigger commands:
reconcile any orphaned attempt marker, check `completed_count >= ceiling`,
and — if not blocked — persist an attempt, retrigger, and promote to
completed as soon as any mention is confirmed submitted. If blocked,
present a three-way human gate (authorize new ceiling / deny / pause)
instead of retriggering. Created
`src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md` with the
full mechanism (state schema, ordering, promotion rule, crash-recovery
reconciliation, explicit scope). Extended
`src/lrh/skills/lrh-land/references/land-workflow.md`'s CHAIN-NOTE
`stops`/`note` field docs to cover round-cap crossings and distinguish
the counter from `cycles`. Added a brief note to
`project/executions/README.md` about the new `round_state/` subdirectory
(non-`.md` JSON files, outside `lrh validate`'s scan). Mirrored both
skill trees to `.claude/skills/`.

Storage/promotion design decisions (left as implementation-time detail by
the WI) documented in the PR body and `round-cap-gate.md`: one JSON file
per PR under `project/executions/round_state/`, not fields on the
execution record, since round state must survive across multiple separate
`/lrh-confirm-fixes` invocations for the same PR.

Did a self-review pass before opening the PR and caught one real issue in
my own draft: a promotion-rule cross-reference ("per step 1's rule")
pointed at the reconciliation step rather than a clearly-stated promotion
rule — the same class of fragile-reference bug review caught repeatedly
on the planning PR (#444). Fixed by stating the promotion rule once,
explicitly, in step 3, and having the concrete retrigger-command section
reference that instead.

Opened [PR #445](https://github.com/xenotaur/logical_robotics_harness/pull/445)
from branch `xenotaur/feat/wi-review-round-escalation-gate-impl`.

# Validation

- `lrh validate`: 0 errors, 1 pre-existing warning unrelated to this change.
- `scripts/version tools`: ruff 0.15.12, black 26.3.1.
- `scripts/format --check --diff`: clean, 179 files unchanged.
- `scripts/lint`: all checks passed.
- `scripts/test`: 808 tests, OK.
- `diff -r src/lrh/skills/lrh-confirm-fixes/ .claude/skills/lrh-confirm-fixes/`
  and `diff -r src/lrh/skills/lrh-land/ .claude/skills/lrh-land/`: no
  differences.

# Follow-up

- `/lrh-review-response` / `/lrh-confirm-fixes` should run next to verify
  and land this PR.
- `session_transcript: pending` should be updated once resolvable.
