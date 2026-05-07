---
execution_id: 2026_05_07_04_58_26_IMPLEMENT_WORKSTREAM_VALIDATION_MVP
prompt_id: PROMPT(WI-WORKSTREAM-VALIDATION-MVP:IMPLEMENT_WORKSTREAM_VALIDATION_MVP)[2026-05-06T11:05:00-04:00]
work_item: WI-WORKSTREAM-VALIDATION-MVP
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-07T04:58:26+00:00
---

# Summary

Implemented the Workstream Validation MVP for single-file workstreams under
`project/workstreams/<status>/WS-*.md`. The validator now checks required MVP
frontmatter fields, kind/status/stage vocabularies, duplicate workstream IDs, the
documented `WS-` ID prefix convention, and bucket/status drift.

# Result

Integrated workstream diagnostics into the existing `lrh validate` control-plane
validation path. Bucket/status mismatches are reported as warnings because
status metadata is authoritative and bucket placement is navigational. The change
also adds focused unit tests for valid and invalid workstream examples and
updates `project/workstreams/README.md` to describe current validation coverage.

# Validation

- `scripts/version tools` passed before task-phase validation.
- `python -m unittest tests.workstreams_tests.validator_test` passed.
- `scripts/format --check` initially reported that the new validator test needed
  formatting.
- `scripts/format tests/workstreams_tests/validator_test.py` reformatted the new
  test file.
- `scripts/format --check` passed after formatting.
- `scripts/lint` passed.
- `scripts/test` passed.

# Follow-up

Recommended next step: generate or run the Planning-Tree Relationship MVP prompt
to add focused parent/child relationship validation without expanding into
snapshot integration, organizer behavior, or runtime orchestration.
