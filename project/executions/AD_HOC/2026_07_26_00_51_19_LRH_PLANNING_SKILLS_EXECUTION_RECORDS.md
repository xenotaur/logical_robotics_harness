---
execution_id: 2026_07_26_00_51_19_LRH_PLANNING_SKILLS_EXECUTION_RECORDS
prompt_id: PROMPT(AD_HOC:LRH_PLANNING_SKILLS_EXECUTION_RECORDS)[2026-07-26T00:49:58-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/424
commit: 1d686797cb5b87c58056b496f4b98a847347f860
created_at: 2026-07-26T00:51:19-04:00
agent: claude_app
instruction_source: ad_hoc conversation — add execution-record creation to lrh-workstream, lrh-work-item, lrh-proposal
session_transcript: claude-app:6e928047-e545-42f5-b524-af2d72b55df8
---

# Summary

Give `/lrh-workstream`, `/lrh-work-item`, and `/lrh-proposal` an
execution-record-creation step, mirroring `/lrh-implement`'s Steps 3 and 9:
mint a prompt ID + idempotence check before each skill's confirm gate, then
create and push an `in_progress` execution record alongside the opened PR.
Confirmed prior gap: LCATS PR #155 (`/lrh-workstream`) and PR #157
(`/lrh-work-item`) both opened with zero primary execution records.

# Result

- Added a new "Instruction phase (mint prompt ID + idempotence check)" step
  before the confirm gate in all three skills' `SKILL.md`, renumbering
  subsequent steps.
- Added a new "Create execution record" step immediately after each skill's
  "Commit and open PR" step, populating `agent`, `instruction_source`,
  `session_transcript` and pushing the record to the open PR.
- Updated each skill's Quality Checklist and "What This Skill Does Not Do"
  section to reflect the new behavior.
- Added `references/execution-record.md` to each of the three skill
  directories, describing the mint/check/record commands and field
  conventions, scoped to that skill's own artifact ID as the bucket
  (`WS-*`, `WI-*`, `PROP-*`).
- Updated `lrh-work-item/references/lrh-work-item-workflow.md`'s lifecycle
  diagram and Path 1 closeout guidance to describe the new record's
  lifecycle.
- `/lrh-implement`, `/lrh-review-response`, `/lrh-confirm-fixes` untouched.
- Kept `src/lrh/skills/` and `.claude/skills/` mirrors in sync (`diff -r`
  confirmed identical after each change).

# Validation

- `lrh validate` — 0 errors (1 pre-existing, unrelated warning:
  `PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on `WS-LRH-ASSISTANTS`).
- `diff -r .claude/skills/{lrh-workstream,lrh-work-item,lrh-proposal}
  src/lrh/skills/...` — no differences.

# Follow-up

- `/lrh-proposal`'s execution-record gap was inferred by analogy to the two
  confirmed incidents, not directly observed — worth confirming against a
  real `/lrh-proposal` PR once one is run under this change.
- `session_transcript` above uses the host session id; update if this
  session is resumed under a different id before the PR lands.
