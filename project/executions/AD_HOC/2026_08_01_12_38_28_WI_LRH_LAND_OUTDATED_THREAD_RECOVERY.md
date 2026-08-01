---
execution_id: 2026_08_01_12_38_28_WI_LRH_LAND_OUTDATED_THREAD_RECOVERY
prompt_id: PROMPT(AD_HOC:WI_LRH_LAND_OUTDATED_THREAD_RECOVERY)[2026-08-01T12:34:17-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/457
commit: 96da0ef2ae8840f47db55081d89bfbf6b932c9b1
created_at: 2026-08-01T12:38:28-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-LAND-OUTDATED-THREAD-RECOVERY.md
session_transcript: claude-app:61881211-bfd7-40cb-8080-33938a265398
---

# Summary

Creates WI-LRH-LAND-OUTDATED-THREAD-RECOVERY, the Layer 2 (governed
skill-flow) work item from PROP-OUTDATED-THREAD-RECOVERY: the live-gated
recovery path in `/lrh-land` Step 4/5, depending on
WI-REVIEW-RESPONSE-INCLUDE-THREAD.

# Result

Wrote `project/work_items/proposed/WI-LRH-LAND-OUTDATED-THREAD-RECOVERY.md`.
`depends_on: [WI-REVIEW-RESPONSE-INCLUDE-THREAD]` — both files coexist on
this branch so the reference resolves under `lrh validate` without
tripping the parallel-branch depends_on limitation.

# Validation

lrh validate — 0 errors, 1 pre-existing unrelated warning
(`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on `WS-LRH-ASSISTANTS`)

# Follow-up

- Update `project/design/backlog.md`'s "lrh request review_response
  cannot surface a specific outdated-but-unresolved thread" entry to
  link/close against this item and WI-REVIEW-RESPONSE-INCLUDE-THREAD.
- Offer a WS-SKILLS-EXECUTE workstream update (add both new WI IDs to
  its work_items list) before opening the PR.
- Populate `pr:`/`commit:` once the branch is pushed and the PR opened.
- Update `session_transcript` to the final host session id if it differs
  after the session ends.
