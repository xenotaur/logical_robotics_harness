---
execution_id: 2026_09_22_06_29_39_WI_EXPORT_ADAPTER_DESCRIPTOR_LEVEL_COLLISION_CHECK_REVIEW
prompt_id: PROMPT(AD_HOC:WI_EXPORT_ADAPTER_DESCRIPTOR_LEVEL_COLLISION_CHECK_REVIEW)[2026-09-22T06:29:36+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_09_20_02_08_50_WI_EXPORT_ADAPTER_DESCRIPTOR_LEVEL_COLLISION_CHECK
pr: https://github.com/xenotaur/logical_robotics_harness/pull/677
commit: 
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/677
session_transcript: pending
created_at: 2026-09-22T06:29:39+00:00
---

# Summary

Address two review threads on PR #677 (Codex r4055734384, Copilot r4055735365):
the work item's Validation bullets used raw `pytest`/`ruff`/`black` instead of
this repo's canonical `scripts/*` wrappers.

# Result

Valid and feasible; both threads flag the same defect. Edited
`project/work_items/proposed/WI-EXPORT-ADAPTER-DESCRIPTOR-LEVEL-COLLISION-CHECK.md`:
replaced the Validation bullets and Acceptance Criterion 5 to require
`scripts/version tools`, `scripts/test`, `scripts/lint`,
`scripts/format --check --diff`, and `lrh validate` instead of raw
`pytest`/`ruff check`/`black --check`.

# Validation

`PYTHONPATH=src lrh validate`: 0 errors, 0 warnings.

# Follow-up

None.
