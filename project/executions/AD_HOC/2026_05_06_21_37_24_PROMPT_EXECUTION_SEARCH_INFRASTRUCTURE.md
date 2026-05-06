---
execution_id: 2026_05_06_21_37_24_PROMPT_EXECUTION_SEARCH_INFRASTRUCTURE
prompt_id: PROMPT(AD_HOC:PROMPT_EXECUTION_SEARCH_INFRASTRUCTURE)[2026-05-06T12:30:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-06T21:37:24+00:00
---

# Summary

Extract shared prompt execution-record parsing and exact prompt-ID query
infrastructure while preserving the existing `lrh prompt check-execution`
command behavior for PR 1 of the staged prompt execution search and match
implementation.

# Result

Implemented package-owned execution-record modules for typed record parsing,
recursive loading under `project/executions/**`, and exact prompt-ID checks.
Rewired `lrh prompt check-execution` and the legacy compatibility wrappers'
installed CLI path to use the shared query helper without adding match, search,
heuristic, indexing, semantic, ranking, or remote lookup behavior.

Added regression coverage for execution-record parsing, nested loading, exact
lookup, no-match and ambiguity results, and CLI exit/output behavior including
custom `--output-root` handling.

# Validation

- `scripts/version tools` passed with Ruff 0.15.12 and Black 26.3.1 available.
- `python -m unittest tests.assist_tests.prompt_workflow_records_test tests.assist_tests.prompt_workflow_test tests.cli_tests.prompt_test` passed.
- `scripts/test` passed.
- `scripts/lint` passed.

# Follow-up

Future staged PRs can add `lrh match executions` and `lrh search executions` on
top of the shared execution-record infrastructure introduced here.
