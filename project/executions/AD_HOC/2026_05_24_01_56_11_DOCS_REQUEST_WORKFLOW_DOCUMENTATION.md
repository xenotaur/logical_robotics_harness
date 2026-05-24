---
execution_id: 2026_05_24_01_56_11_DOCS_REQUEST_WORKFLOW_DOCUMENTATION
prompt_id: PROMPT(AD_HOC:DOCS_REQUEST_WORKFLOW_DOCUMENTATION)[2026-05-22T10:13:00-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: 
commit: 7dda77c19c4af163ab16ee0400d0591bdee0fa9a
created_at: 2026-05-24T01:56:11+00:00
---

# Summary

Added Diátaxis-style docs for LRH docs-request workflows so maintainers can generate `audit_docs` and `organize_docs` prompts for standard and nested layouts before dogfooding.

# Result

- Added new how-to guides for generating audit and organization prompts.
- Added a new explanation page describing the two-stage audit/organize model and rationale.
- Updated docs navigation/readme pages and CLI request reference to include implemented docs-request behavior, examples, and option accuracy notes.

# Validation

- `python -m lrh.cli.main prompt check-execution --prompt-id 'PROMPT(AD_HOC:DOCS_REQUEST_WORKFLOW_DOCUMENTATION)[2026-05-22T10:13:00-04:00]' --project-root .` (exit 1; confirmed no existing execution records)
- `python -m lrh.cli.main request --help` (pass)
- `python -m lrh.cli.main request audit_docs --help` (pass; currently returns top-level request help)
- `python -m lrh.cli.main request organize_docs --help` (pass; currently returns top-level request help)
- `lrh request --help` (pass)
- `lrh request audit_docs --help` (pass; currently returns top-level request help)
- `lrh request organize_docs --help` (pass; currently returns top-level request help)
- `scripts/version tools` (pass)
- `scripts/lint` (fail: pre-existing Ruff F811 duplicate test class in `tests/assist_tests/request_service_test.py`)
- `scripts/test` (not run because `scripts/lint` failed)

# Follow-up

- Investigate and fix the pre-existing Ruff duplicate-class lint failure in `tests/assist_tests/request_service_test.py`, then rerun canonical lint/test.
