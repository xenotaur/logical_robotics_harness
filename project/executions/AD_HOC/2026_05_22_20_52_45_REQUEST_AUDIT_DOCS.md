---
execution_id: 2026_05_22_20_52_45_REQUEST_AUDIT_DOCS
prompt_id: PROMPT(AD_HOC:REQUEST_AUDIT_DOCS)[2026-05-22T10:11:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-22T20:52:45+00:00
---

# Summary

Implemented `lrh request audit-docs` as a reusable prompt-template workflow with
request catalog wiring, CLI options for repository/docs/control/package roots,
and template variables for deterministic prompt rendering.

# Result

Added `request/audit_docs.md`, request-catalog registration, and request-service
variable handling for audit request inputs. Added focused tests for default and
nested root rendering and prompt-content requirements.

# Validation

- `scripts/version tools` (pass; tooling versions printed, with optional tools absent)
- `scripts/test tests/assist_tests/request_service_test.py tests/assist_tests/request_catalog_test.py tests/cli_tests/request_test.py` (pass; request-service suite executed successfully)

# Follow-up

- Add dedicated CLI/integration tests for `lrh request audit-docs --out` and
  repeated `--package-root` handling in full command execution paths.
