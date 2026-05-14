---
execution_id: 2026_05_14_06_33_04_REQUEST_DISCOVERABILITY
prompt_id: PROMPT(AD_HOC:REQUEST_DISCOVERABILITY)[2026-05-05T13:55:00-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: 
commit: 
created_at: 2026-05-14T06:33:04+00:00
---

# Summary

Added request-catalog discoverability to `lrh request` so users can list cataloged request names by category and describe requests by canonical or legacy name without inspecting template files.

# Result

Implemented `lrh request list`, `lrh request list --category <category>`, and `lrh request describe <name>`. Description output includes the canonical name, category, description, legacy names, template path, implementation target, usage line, and the legacy name used when applicable. Updated README guidance and added CLI tests for listing, category filtering, canonical description, legacy description, and unknown-name errors.

# Validation

- `scripts/version tools`
- `python -m unittest tests.cli_tests.request_test`
- `scripts/test`
- `scripts/lint`
- `scripts/format --check --diff`
- `scripts/validate`

# Follow-up

No immediate follow-up required. Grouped execution commands and short aliases remain intentionally out of scope.
