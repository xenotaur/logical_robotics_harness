---
execution_id: 2026_08_05_06_22_07_WI_LAND_PRIMARY_RECORD_SUFFIX_COLLISION
prompt_id: PROMPT(AD_HOC:WI_LAND_PRIMARY_RECORD_SUFFIX_COLLISION)[2026-08-05T06:20:38+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/488
commit: 902a4e0dfcea5127d1236ccfc69421f63f093050
created_at: 2026-08-05T06:22:07+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LAND-PRIMARY-RECORD-SUFFIX-COLLISION.md
session_transcript: claude-app:23a15fdd-6d6c-4d84-a7be-960a54769157
---

# Summary

Filed `WI-LAND-PRIMARY-RECORD-SUFFIX-COLLISION`, a work item to fix the
`/lrh-land`/`/lrh-confirm-fixes`/`/lrh-review-response` primary-record
search substring-collision bug: a bare `_REVIEW.md`/`_CONFIRM.md`/
`_CLOSEOUT_NOTE.md`/`_SELFREVIEW.md` filename-suffix exclusion, not a
provenance check, so a primary record whose own topic slug ends in one
of those words self-excludes and is misclassified as absent.

# Result

Created `project/work_items/proposed/WI-LAND-PRIMARY-RECORD-SUFFIX-COLLISION.md`,
opened PR #488. Confirmed no duplicate work item or proposal exists; the
bug is documented (but not fixed) in `land-workflow.md`'s own "Known
limitation, not fixed by this exclusion list" note, cited as prior art
in the WI's Problem/Context section. Set `related_workstreams:
[WS-SKILLS-EXECUTE]` to match its sibling `WI-LRH-LAND-OUTDATED-THREAD-RECOVERY`
(same workstream, different `/lrh-land` gap) — not yet added to that
workstream's `work_items:` frontmatter list, offered separately.

# Validation

- `lrh validate`: 0 errors, 0 warnings

# Follow-up

- Offer to add `WI-LAND-PRIMARY-RECORD-SUFFIX-COLLISION` to
  `WS-SKILLS-EXECUTE.md`'s `work_items:` list (Step 11 offer, not yet
  accepted/declined at record-creation time).
- `session_transcript: pending` should be updated to
  `claude-app:<host-uuid-stem>` before archiving.
