---
execution_id: 2026_05_04_23_04_58_TEMPLATE_OVERRIDE_DOCS_DIAGNOSTICS
prompt_id: PROMPT(AD_HOC:TEMPLATE_OVERRIDE_DOCS_DIAGNOSTICS)[2026-05-04T15:02:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-04T23:04:58+00:00
---

# Summary

Document and diagnose assist template overrides for request templates.

# Result

Added `lrh request templates list` and `lrh request templates where` diagnostics that reuse existing template resolution and avoid printing template contents. Updated assist documentation with override locations, package fallback behavior, and diagnostic examples. Review feedback made fallback/missing diagnostics tests hermetic and fixed `where review_response.md` normalization.

# Validation

- `scripts/version tools`
- `scripts/format --check` (failed before formatting; request CLI and request CLI tests needed Black formatting)
- `scripts/format`
- `scripts/format --check`
- `scripts/lint`
- `python -m unittest tests.assist_tests.request_cli_test`
- `scripts/test`
- Review repair validation: `scripts/version tools`
- Review repair validation: `scripts/format --check --diff` (failed before formatting; request CLI and request CLI tests needed Black formatting)
- Review repair validation: `scripts/format`
- Review repair validation: `scripts/format --check --diff`
- Review repair validation: `scripts/lint`
- Review repair validation: `scripts/test`

# Follow-up

None.
