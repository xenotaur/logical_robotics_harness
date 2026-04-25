---
execution_id: 2026_04_25_03_07_01_WORK_ITEM_PROMPT_CORE_READINESS_AND_PROMPT_ID
prompt_id: PROMPT(AD_HOC:WORK_ITEM_PROMPT_CORE)[2026-04-24T20:05:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_04_25_02_59_19_WORK_ITEM_PROMPT_CORE_BLOCKED_BOOL_VALIDATION
pr: draft
commit: cefe7c7fbb6aaa453b8c3bc927097b38c3c0993a
created_at: 2026-04-25T03:07:01+00:00
---

# Summary

Addressed review feedback to tighten work-item readiness gating and remove fixed prompt ID behavior in codex prompt generation.

# Result

Missing key sections (`Scope`, `Required Changes`, `Acceptance Criteria`, `Validation`) now block prompt readiness rather than surfacing only warnings. Added explicit `--prompt-id` support and dynamic prompt ID generation from work-item ID + timestamp when not provided, replacing the previous hard-coded prompt ID.

# Validation

- python -m unittest tests.assist_tests.work_item_prompt_core_test tests.assist_tests.request_service_test tests.assist_tests.request_cli_test
- scripts/format
- scripts/lint
- scripts/test

# Follow-up

- Consider tightening readiness policy further if future schema requires additional sections to be mandatory for codex suitability.
