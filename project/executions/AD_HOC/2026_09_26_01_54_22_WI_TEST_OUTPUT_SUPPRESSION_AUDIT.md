---
execution_id: 2026_09_26_01_54_22_WI_TEST_OUTPUT_SUPPRESSION_AUDIT
prompt_id: PROMPT(AD_HOC:WI_TEST_OUTPUT_SUPPRESSION_AUDIT)[2026-09-26T01:48:54+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/731
commit: 
agent: claude_app
instruction_source: project/work_items/proposed/WI-TEST-OUTPUT-SUPPRESSION-AUDIT.md
session_transcript: claude-app:42f65eea-a5d0-4b14-b12d-fdac79928916
created_at: 2026-09-26T01:54:22+00:00
---

# Summary

Created `WI-TEST-OUTPUT-SUPPRESSION-AUDIT` (planning-only PR — this record
documents the item's creation, not its implementation).

# Result

Filed a same-session audit's findings as a work item: LRH's `scripts/test`
leaks extensive print noise because ~30 of 116 test files invoke CLI/library
code in-process without capturing stdout/stderr, traced to two concrete
chains (`tests/cli_tests/pii_test.py` -> `src/lrh/cli/main.py`'s pii-scan
print paths; `tests/dev_tests/release_smoke_test.py` ->
`src/lrh/dev/release_smoke.py`'s progress prints). Compared against the
sibling LCATS repo's `WI-TEST-0107`/`lcats.utils.capture` prior art
(verified directly, not taken on the researching subagent's word alone).
Prior-art check: no in-repo duplicate, no open demand match. Work item
created at `project/work_items/proposed/WI-TEST-OUTPUT-SUPPRESSION-AUDIT.md`,
PR opened at https://github.com/xenotaur/logical_robotics_harness/pull/731.

# Validation

- `lrh validate` — 0 errors, 0 warnings (after adding `anthony` to
  `contributors:` to clear an `OWNER_NOT_IN_CONTRIBUTORS` warning).

# Follow-up

None from this planning session. Implementation is a separate future
session (`/lrh-implement WI-TEST-OUTPUT-SUPPRESSION-AUDIT` or manual);
per the work item's own Risk Notes, the implementer may reasonably split
it into more than one PR.
