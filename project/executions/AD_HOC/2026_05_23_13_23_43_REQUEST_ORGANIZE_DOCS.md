---
execution_id: 2026_05_23_13_23_43_REQUEST_ORGANIZE_DOCS
prompt_id: PROMPT(AD_HOC:REQUEST_ORGANIZE_DOCS)[2026-05-22T10:12:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-23T13:23:43+00:00
---

# Summary

Implemented LRH `request organize_docs` prompt-template support, including CLI/catalog wiring,
request variable support for `--phase`, template authoring, targeted request-template tests,
and a minimal CLI reference note.

# Result

- Added cataloged request name `organize-docs` with legacy alias `organize_docs`.
- Added `--phase` option to `lrh request` parser and exported `REQUEST_ORGANIZE_DOCS_PHASE`
  for template interpolation.
- Added new request template `src/lrh/assist/templates/request/organize_docs.md` with
  one-scoped-PR, phase-bounded, Diátaxis, docs/control boundary, and execution-record guidance.
- Added/updated tests for organize-docs rendering and catalog coverage.
- Added a concise CLI reference note clarifying that the command generates prompts only.

# Validation

- `scripts/version tools`
- `scripts/lint` (failed initially due to test syntax + formatting; fixed in same run)
- `black src/lrh/assist/request_catalog.py`
- `scripts/test`

# Follow-up

- If needed, future work can add stronger validation/error messaging around missing `--audit`
  and explicit phase enum constraints at CLI level.
