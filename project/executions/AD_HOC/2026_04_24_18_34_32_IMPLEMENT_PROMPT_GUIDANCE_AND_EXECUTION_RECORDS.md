---
execution_id: 2026_04_24_18_34_32_IMPLEMENT_PROMPT_GUIDANCE_AND_EXECUTION_RECORDS
prompt_id: PROMPT(WI-PROMPT-WORKFLOW:IMPLEMENT_PROMPT_GUIDANCE_AND_EXECUTION_RECORDS)[2026-04-24T00:00:00-04:00]
work_item: AD_HOC
status: landed
rerun_of:
pr:
commit:
created_at: 2026-04-24T18:34:32+00:00
---

# Summary

Implemented lightweight prompt-workflow guidance and helper scripts for prompt IDs and execution records. No `WI-PROMPT-WORKFLOW` work item exists yet, so this execution is tracked under `AD_HOC`.

# Result

Added `PROMPTS.md`, documented execution-record schema in `project/executions/README.md`, added `scripts/prompts/label-prompt` and `scripts/prompts/record-execution`, updated related READMEs plus `AGENTS.md` and `STYLE.md`, and added focused script tests.

# Validation

Ran targeted script tests for prompt workflow helpers and both script `--help` checks.

# Follow-up

Optionally add a dedicated `WI-PROMPT-WORKFLOW` work item later if this workflow evolves beyond lightweight prompt traceability.
