---
execution_id: 2026_07_29_01_38_46_LRH_EXECUTION_RECORD_CREATION_B69A83_REVIEW
prompt_id: PROMPT(AD_HOC:LRH_EXECUTION_RECORD_CREATION_B69A83_REVIEW)[2026-07-29T01:32:26-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_07_26_00_51_19_LRH_PLANNING_SKILLS_EXECUTION_RECORDS
pr: https://github.com/xenotaur/logical_robotics_harness/pull/424
commit: 
created_at: 2026-07-29T01:38:46-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/424
session_transcript: claude-app:6e928047-e545-42f5-b524-af2d72b55df8
---

# Summary

Address PR #424 review feedback from Copilot and Codex: fix a P1 design
flaw where the new planning skills' creation-record `--work-item` bucket
would cause `/lrh-closeout` to auto-resolve the freshly created, not-yet-
implemented work item; fix a related but lower-severity closeout-lookup
friction issue for the workstream/proposal skills; correct an inaccurate
slug/timestamp disambiguation claim; and require real narrative content in
place of generated TODO placeholders before pushing an execution record.

# Result

- `/lrh-work-item`, `/lrh-workstream`, `/lrh-proposal`: changed the
  "Instruction phase" mint step and "Create execution record" step to use
  the `AD_HOC` bucket (the `lrh prompt label` default) instead of the newly
  minted `WI-*`/`WS-*`/`PROP-*` ID. Rationale documented inline and in each
  skill's `references/execution-record.md`: `/lrh-closeout`'s decision
  matrix resolves any work item found via the execution record's
  `work_item:` bucket, so bucketing the *creation* record under the new
  WI's own ID would resolve it the moment the planning PR merges, before
  any implementation happens (confirmed against
  `.claude/skills/lrh-closeout/references/closeout-workflow.md`). For
  `/lrh-workstream` and `/lrh-proposal` the failure mode is milder (a
  spurious "work item not found" prompt at closeout rather than a wrongful
  resolution), but the same `AD_HOC` fix applies for consistency.
- `/lrh-work-item/references/execution-record.md`: reworded the claim that
  the creation record and the future `/lrh-implement` record are
  "disambiguated by their slugs and timestamps" — both records in fact
  derive the same lower-kebab slug from the same WI ID, so it is the
  `AD_HOC` vs. `<ID>` bucket (plus timestamp) that disambiguates them, not
  the slug.
- All three skills' "Create execution record" step and Quality Checklist
  now instruct replacing the generated `# Summary`/`# Result`/
  `# Validation`/`# Follow-up` TODO placeholders with real content before
  committing, since `/lrh-closeout` only edits frontmatter when landing and
  would otherwise ship a narrative-free record as `landed`
  (`AGENTS.md`'s evidence policy).
- Kept `src/lrh/skills/` and `.claude/skills/` mirrors in sync (`diff -r`
  confirmed identical).

# Validation

- `scripts/version tools`, `scripts/format --check --diff`, `scripts/lint`,
  `scripts/test` (808 tests, all passing), `lrh validate` (0 errors, 1
  pre-existing unrelated warning on `WS-LRH-ASSISTANTS`) — all run and
  passing after the fix.
- Pushed directly to the open PR branch
  (`claude/lrh-execution-record-creation-b69a83`, commit `1fb698a`).

# Follow-up

- None outstanding from this round. `/lrh-confirm-fixes` should verify these
  fixes against the current diff before merge.
