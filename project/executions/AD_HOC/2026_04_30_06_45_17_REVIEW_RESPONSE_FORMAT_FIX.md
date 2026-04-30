---
execution_id: 2026_04_30_06_45_17_REVIEW_RESPONSE_FORMAT_FIX
prompt_id: PROMPT(AD_HOC:REVIEW_RESPONSE_FORMAT_FIX)[2026-04-30T02:38:05-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/127
commit: 7c9f3b7
created_at: 2026-04-30T06:45:17+00:00
---

# Summary

Fix `lrh request review_response` to emit the required repair-prompt preamble and unresolved-comment block instead of reviewer-reply drafting instructions.

# Result

Updated the review-response template to the required fixed preamble/separator and switched unresolved-comment rendering to reuse `lrh github unresolved` review formatting through `formatters.format_threads_review(..., state="unresolved")`. Added regression assertions to lock exact prefix/separator presence, unresolved-thread formatting cues, and absence of obsolete language.

# Validation

- `python -m unittest tests.assist_tests.request_service_test tests.assist_tests.request_cli_test`
- `scripts/lint`
- `scripts/test`

# Follow-up

- Record PR/commit references when available.
