---
execution_id: 2026_10_06_02_17_34_WI_LRH_GH_ERROR_CLASSIFICATION
prompt_id: PROMPT(WI-LRH-GH-ERROR-CLASSIFICATION:WI_LRH_GH_ERROR_CLASSIFICATION)[2026-10-06T01:55:48+00:00]
work_item: WI-LRH-GH-ERROR-CLASSIFICATION
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/773
commit: 
agent: codex_app
instruction_source: WI-LRH-GH-ERROR-CLASSIFICATION
session_transcript: pending
created_at: 2026-10-06T02:17:34+00:00
---

# Summary

Implement distinct LRH GitHub-wrapper diagnostics for invalid project roots,
missing `gh`, network/authentication/API command failures, and malformed JSON,
with hermetic unittest coverage.

# Result

Added explicit project-root validation, race-safe cwd classification, sanitized
credential-aware stderr diagnostics, network/authentication/API/command failure
categories, and distinct malformed-JSON handling. Added unittest coverage for
each failure class while preserving successful wrapper behavior.

# Validation

- `scripts/format --check --diff`: passed with the repository-pinned toolchain.
- `scripts/lint`: passed.
- `scripts/test`: 1,913 tests passed.
- `lrh validate`: 0 errors, 0 warnings.
- `git diff --check`: passed.

# Follow-up

PR #773 is open for review. Review findings must be addressed and confirmed
before merge; after merge, closeout will land the execution records and resolve
the work item.
