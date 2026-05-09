---
execution_id: 2026_05_09_02_30_22_DOCUMENT_PROMPT_EXECUTION_SEARCH_WORKFLOW
prompt_id: PROMPT(AD_HOC:DOCUMENT_PROMPT_EXECUTION_SEARCH_WORKFLOW)[2026-05-07T02:15:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-09T02:30:22+00:00
---

# Summary

Document the prompt execution lookup, prompt-file matching, and execution-record
search workflow after the staged implementation landed.

# Result

Updated the main README prompt workflow guidance, execution-record README, and
proposal indexes to explain the role of prompt execution records, distinguish
authoritative exact lookup from convenience matching and exploratory search, and
include practical examples using the implemented command grammar.

# Validation

- `scripts/version tools` passed for LRH, Python, Ruff, Black, Pyright, and pip;
  Pylint and Conda are not installed in this environment.
- `lrh prompt check-execution --prompt-id 'PROMPT(AD_HOC:DOCUMENT_PROMPT_EXECUTION_SEARCH_WORKFLOW)[2026-05-07T02:15:00-04:00]' --project-root .` reported no prior exact record before work began.
- `lrh prompt check-execution --help` passed.
- `lrh match --help` passed.
- `lrh match executions --help` passed.
- `lrh search --help` passed.
- `lrh search executions --help` passed.
- `scripts/test` passed: 394 tests.
- `scripts/lint` passed: Ruff checks passed and Black would leave 126 files unchanged.

# Follow-up

After this PR is merged, update this record to `landed` and fill the `pr`
and `commit` metadata. Future changes that add heuristic or fuzzy matching
should continue to label those results as non-authoritative unless a new
accepted design changes the soft-idempotence rule.
