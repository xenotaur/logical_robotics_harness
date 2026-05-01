---
execution_id: 2026_05_01_00_07_36_UPDATE_PROMPT_TEMPLATES_FOR_PORTABILITY
prompt_id: PROMPT(WI-INSTALLED-PROMPT-WORKFLOW:UPDATE_PROMPT_TEMPLATES_FOR_PORTABILITY)[2026-04-29T22:08:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-01T00:07:36+00:00
---

# Summary

Updated Codex prompt-generation template language to be portable across arbitrary client repositories, including conditional repository-guidance rules, portable execution-record guidance, and non-assumptive validation command guidance.

`WI-INSTALLED-PROMPT-WORKFLOW` was not present in repository work items, so this execution is recorded under `AD_HOC`.

# Result

- Updated `codex_prompt_from_work_item` request template to:
  - conditionally read `AGENTS.md`, `STYLE.md`, and `PROMPTS.md`
  - prefer `lrh prompt record-execution`
  - include fallbacks for non-installed/non-bootstrapped repositories
  - avoid hard assumptions about `scripts/test`, `scripts/lint`, and local scripts
- Updated assist workflow README to document the same portable execution-record policy.
- Added request-template tests for the new portable guidance and anti-assumption checks.

# Validation

- `python -m unittest tests.assist_tests.request_templates_test tests.assist_tests.work_item_prompt_core_test`
- `scripts/test`

# Follow-up

- After PR merge, update this execution record with PR number, commit SHA, and final status.
