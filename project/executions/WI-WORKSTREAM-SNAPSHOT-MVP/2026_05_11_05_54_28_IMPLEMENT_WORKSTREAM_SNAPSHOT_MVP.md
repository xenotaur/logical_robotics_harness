---
execution_id: 2026_05_11_05_54_28_IMPLEMENT_WORKSTREAM_SNAPSHOT_MVP
prompt_id: PROMPT(WI-WORKSTREAM-SNAPSHOT-MVP:IMPLEMENT_WORKSTREAM_SNAPSHOT_MVP)[2026-05-06T11:20:00-04:00]
work_item: WI-WORKSTREAM-SNAPSHOT-MVP
status: landed
rerun_of: 
pr: 
commit: 
created_at: 2026-05-11T05:54:28+00:00
---

# Summary

Implemented read-only workstream visibility for `lrh snapshot project`.

# Result

- Added a `## Workstreams` project-snapshot section that reports metadata-authoritative counts for `proposed`, `active`, `resolved`, and `abandoned` workstreams.
- Added an active-workstream listing with workstream ID, title, stage, status, and simple relationship-derived child/work-item counts when available.
- Reused the existing workstream loader/model and planning-tree relationship index without adding mutation, organize/tidy behavior, stage advancement, execution readiness, automation, orchestration, or `lrh run`.
- Included workstream/planning diagnostics in the snapshot section so bucket/status drift is visible without being repaired.
- Added focused snapshot tests for no-workstream state, multi-bucket counts, active-workstream listing, ignored README/placeholder files, and bucket/status drift reporting.
- Updated `project/workstreams/README.md` to note the new read-only snapshot summary and keep organizer/tidy behavior deferred.

# Validation

- `scripts/version tools` confirmed the task-phase tool versions available in this environment.
- `scripts/format --check` passed.
- `scripts/lint` passed.
- `scripts/test` passed.

# Follow-up

Review whether the snapshot fields are useful in day-to-day control-plane review before generating the Workstream Organize/Tidy MVP prompt.
