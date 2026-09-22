---
execution_id: 2026_09_21_19_13_04_WI_LRH_MEMORY_REPAIR_PRESERVE_METADATA
prompt_id: PROMPT(AD_HOC:WI_LRH_MEMORY_REPAIR_PRESERVE_METADATA)[2026-09-21T19:02:39+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/687
commit: 
created_at: 2026-09-21T19:13:04+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-MEMORY-REPAIR-PRESERVE-METADATA.md
session_transcript: pending
---

# Summary

Created proposed deliverable work item WI-LRH-MEMORY-REPAIR-PRESERVE-METADATA, making `lrh memory repair` preserve unknown frontmatter keys so a legacy-memory `authored_by` backfill loses no Claude Code auto-memory metadata. Creation only; no code changes.

# Result

Added project/work_items/proposed/WI-LRH-MEMORY-REPAIR-PRESERVE-METADATA.md and opened PR #687. Prior-art check found no duplicate or existing demand. Research measured that a YAML round trip rewrites an unquoted timestamp, so the WI requires textual preservation. Readiness: prompt_ready yes, no warnings.

# Validation

`lrh validate`: 0 errors, 0 warnings. `lrh work-items readiness`: prompt_ready yes.

# Follow-up

- Implement via /lrh-execute WI-LRH-MEMORY-REPAIR-PRESERVE-METADATA, then back up and backfill authored_by on the 14 legacy memories (separate operation).
- The WI asks the implementer to record whether write/import/transfer overwrite has the same key-loss.
- Update session_transcript from pending at closeout.
