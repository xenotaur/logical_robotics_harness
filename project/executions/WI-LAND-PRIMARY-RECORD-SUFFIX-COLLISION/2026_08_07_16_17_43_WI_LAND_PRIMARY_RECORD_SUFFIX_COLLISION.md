---
execution_id: 2026_08_07_16_17_43_WI_LAND_PRIMARY_RECORD_SUFFIX_COLLISION
prompt_id: PROMPT(WI-LAND-PRIMARY-RECORD-SUFFIX-COLLISION:WI_LAND_PRIMARY_RECORD_SUFFIX_COLLISION)[2026-08-07T15:58:14+00:00]
work_item: WI-LAND-PRIMARY-RECORD-SUFFIX-COLLISION
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/508
commit: ea0de37548ef5f8b31b606b7d0518bc26aca3abc
agent: claude_app
instruction_source: project/work_items/proposed/WI-LAND-PRIMARY-RECORD-SUFFIX-COLLISION.md
session_transcript: claude-app:ad0eb54f-df82-4b10-9450-9cb763e47b7f
created_at: 2026-08-07T16:17:43+00:00
---

# Summary

Implement the fix for `WI-LAND-PRIMARY-RECORD-SUFFIX-COLLISION`: replace
the bare filename-suffix exclusion used by `/lrh-land` Step 1,
`/lrh-confirm-fixes`'s `rerun_of` search, and `/lrh-review-response`'s
`rerun_of` search with a provenance check that distinguishes primary from
side records by actual slug-appending relationship rather than a
coincidental suffix match. Run via `/lrh-execute`, chained into `/lrh-land`
for review, confirm, merge, and closeout.

# Result

Added a "Primary vs. side-record provenance check" section to
`src/lrh/skills/lrh-land/references/land-workflow.md`: strips each
candidate's leading timestamp from its `execution_id` to get its semantic
slug, then classifies a candidate as a side record only if BOTH (a) its
slug ends in one of the four reserved suffixes (`_REVIEW`, `_CONFIRM`,
`_CLOSEOUT_NOTE`, `_SELFREVIEW`) AND (b) stripping that suffix yields a
slug matching another record's slug elsewhere under
`project/executions/`. Updated `/lrh-land/SKILL.md` Step 1 and the
`rerun_of` search sites in `/lrh-confirm-fixes/SKILL.md` +
`references/confirm-fixes-workflow.md` and
`/lrh-review-response/SKILL.md` + `references/review-response-workflow.md`
to use the corrected algorithm. Removed the old "Known limitation, not
fixed by this exclusion list" note. Mirrored all six changed files to
`.claude/skills/`.

Ran a proactive diff-mode `/lrh-self-review` before pushing (clean pass,
no findings; see `project/executions/AD_HOC/2026_08_07_16_13_47_WI_LAND_PRIMARY_RECORD_SUFFIX_COLLISION_SELFREVIEW.md`).

# Validation

- Corrected algorithm hand-verified against real `project/executions/`
  data: `WI-SKILLS-LRH-SELF-REVIEW`'s own primary record (slug ends in
  `_SELF_REVIEW`, correctly kept), its genuine `_CLOSEOUT_NOTE`/`_CONFIRM`
  side records (correctly excluded), and the doubled-suffix collision case
  `ADOPT_PROP_LRH_SELF_REVIEW_REVIEW` (correctly excluded while its own
  primary `ADOPT_PROP_LRH_SELF_REVIEW` is correctly kept)
- `diff -r src/lrh/skills/{lrh-land,lrh-confirm-fixes,lrh-review-response}/ .claude/skills/{same}/` → zero output
- `scripts/version tools`, `scripts/format --check --diff`, `scripts/lint` → clean
- `scripts/test` → 1004 tests passed
- `lrh validate` → 0 errors, 0 warnings

# Follow-up

- Address PR #508 review comments via `/lrh-review-response`
- Run `/lrh-confirm-fixes` before merge
- After merge: `/lrh-closeout` to resolve `WI-LAND-PRIMARY-RECORD-SUFFIX-COLLISION`
