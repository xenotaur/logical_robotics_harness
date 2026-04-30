---
execution_id: 2026_04_30_04_33_09_CREATE_INSTALLED_PROMPT_CLI
prompt_id: PROMPT(AD_HOC:CREATE_INSTALLED_PROMPT_CLI)[2026-04-29T22:05:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-04-30T04:33:09+00:00
---

# Summary

Implemented an initial installed LRH prompt workflow CLI slice by adding package-owned
`lrh prompt label` and `lrh prompt record-execution` command paths, plus targeted
unit/CLI coverage and docs updates.

Work item `WI-INSTALLED-PROMPT-WORKFLOW` was not present under `project/work_items/`,
so this execution record is scoped under `AD_HOC`.

# Result

In progress. Core package module and CLI wiring were added, deterministic output shape
was preserved from helper scripts, and explicit `--project-root` support was included.

# Validation

- `scripts/test tests/assist_tests/prompt_workflow_test.py`
- `scripts/test tests/cli_tests/prompt_test.py`
- `scripts/test tests/scripts_tests/prompt_scripts_test.py`

# Follow-up

- Optional follow-up: convert `scripts/prompts/*` to thin wrappers over installed
  package logic once compatibility rollout is complete.
