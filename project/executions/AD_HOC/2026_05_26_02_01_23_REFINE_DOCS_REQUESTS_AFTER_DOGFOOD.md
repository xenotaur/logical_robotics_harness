---
execution_id: 2026_05_26_02_01_23_REFINE_DOCS_REQUESTS_AFTER_DOGFOOD
prompt_id: PROMPT(AD_HOC:REFINE_DOCS_REQUESTS_AFTER_DOGFOOD)[2026-05-22T10:15:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 7187e081c133c20529f60b376ff07a5ebfae7a7e
created_at: 2026-05-26T02:01:23+00:00
---

# Summary

Refined docs-request ergonomics after nested-layout dogfooding by addressing the
recorded `--audit` ambiguity for `organize_docs`, adding focused regression
coverage, and updating user-facing docs/evidence notes without broad workflow
expansion.

# Result

- Added explicit CLI alias `--audit` for `--audit-file` so organize-docs
  shorthand no longer collides with `--audit-output`.
- Added CLI integration coverage for `lrh request organize-docs --audit ...`
  in a nested-root style invocation.
- Updated assist README examples to accurately describe `audit-docs` and
  `organize-docs` request usage, including the `--audit` alias.
- Updated the dogfood audit artifact with PR-6 triage: immediate fix landed,
  broader option-name harmonization deferred, and prior ambiguity semantics now
  superseded.

# Validation

- `scripts/version tools` (pass)
- `scripts/lint` (pass)
- `scripts/test` (pass)
- `python -m lrh.cli.main request audit_docs --help` (pass)
- `python -m lrh.cli.main request organize_docs --help` (pass)
- `lrh request audit_docs --help` (pass)
- `lrh request organize_docs --help` (pass)

# Follow-up

- Keep any broader option naming harmonization (`--audit-file` vs
  `--audit-output`) as separate follow-up work to avoid compatibility churn in
  this focused PR.
