---
execution_id: 2026_09_22_06_35_42_WI_LRH_MEMORY_WRITE_OVERWRITE_PRESERVE_METADATA
prompt_id: PROMPT(AD_HOC:WI_LRH_MEMORY_WRITE_OVERWRITE_PRESERVE_METADATA)[2026-09-22T06:35:29+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/709
commit: 
created_at: 2026-09-22T06:35:42+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-MEMORY-WRITE-OVERWRITE-PRESERVE-METADATA.md
session_transcript: pending
---

# Summary

Created proposed deliverable work item WI-LRH-MEMORY-WRITE-OVERWRITE-PRESERVE-METADATA: fixes write/import/transfer's overwrite key-loss (same defect repair had) and repair's filename-derivation bug (writes to a new, wrong file when name: omits a type prefix the filename carries). Creation only; no code changes.

# Result

Added project/work_items/proposed/WI-LRH-MEMORY-WRITE-OVERWRITE-PRESERVE-METADATA.md and opened PR #709. The filename-derivation bug was discovered and manually remediated live during this session's real-corpus backfill (4 stray duplicate files/index entries removed; 4 originals hand-backfilled; corpus verified clean: 0 malformed/unindexed/legacy, 43 conforming). Prior-art check found no duplicate or existing demand.

# Validation

`lrh validate`: 0 errors, 0 warnings. `lrh work-items readiness`: prompt_ready yes.

# Follow-up

- Implement via /lrh-execute WI-LRH-MEMORY-WRITE-OVERWRITE-PRESERVE-METADATA.
- Update session_transcript from pending at closeout.
