---
execution_id: 2026_05_01_06_03_46_UPDATE_PROMPT_TEMPLATES_FOR_PORTABILITY_RERUN
prompt_id: PROMPT(WI-INSTALLED-PROMPT-WORKFLOW:UPDATE_PROMPT_TEMPLATES_FOR_PORTABILITY)[2026-04-29T22:08:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_05_01_00_07_36_UPDATE_PROMPT_TEMPLATES_FOR_PORTABILITY
pr: 
commit: 
created_at: 2026-05-01T06:03:46+00:00
---

# Summary

Addressed PR review feedback that portability assertions were only checking a template asset while the runtime path for `lrh request codex_prompt_from_work_item` uses `work_item_prompt_core.generate_codex_cloud_prompt`.

# Result

- Updated generated prompt text in `work_item_prompt_core.render_codex_cloud_prompt` to include conditional repository guidance and portable execution-record instructions.
- Updated request-service and prompt-core tests to assert portability behavior on the rendered user-facing prompt output.
- Retained template-level portability checks and aligned runtime-generated output with the same policy.

# Validation

- `python -m unittest tests.assist_tests.request_service_test tests.assist_tests.work_item_prompt_core_test tests.assist_tests.request_templates_test`
- `scripts/test`

# Follow-up

- After PR merge, update this execution record with PR/commit details and final status.
