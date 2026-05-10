---
execution_id: 2026_05_09_23_43_40_DESIGN_PROPOSAL_SNAPSHOT_REPORTING
prompt_id: PROMPT(AD_HOC:DESIGN_PROPOSAL_SNAPSHOT_REPORTING)[2026-05-09T10:15:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-05-09T23:43:40+00:00
---

# Summary

Extend `lrh snapshot project` with compact design-proposal lifecycle and
implementation-traceability reporting using the parsed control-plane
`DesignProposal` model.

# Result

Implemented a `Design Proposals` section in project snapshot context packets.
The section deterministically groups adopted proposals by parsed
`implementation_status`, treats legacy `accepted` as adopted, reports proposals
with missing implementation status as `Adopted / unspecified`, lists superseded
proposals with `superseded_by`, and shows concise `implemented_by` and
`evidence` ID lists for partial or implemented designs. It also surfaces focused
traceability warnings for implemented proposals without implementation/evidence
links, adopted proposals without implementation status, and superseded proposals
without a replacement.

Added a public loader helper for already resolved project directories so
snapshot reporting can reuse the existing design-proposal parser/model without
copying parser logic. Updated snapshot/design-proposal documentation and added
unit coverage for no-proposal output, grouping, traceability display, legacy
`accepted` handling, superseded output, deterministic ordering, and preservation
of existing project snapshot sections.

# Validation

- `lrh prompt check-execution --prompt-id "PROMPT(AD_HOC:DESIGN_PROPOSAL_SNAPSHOT_REPORTING)[2026-05-09T10:15:00-04:00]" --project-root .` found no prior execution records before implementation.
- `scripts/version tools` completed before task-phase validation; Black and Ruff
  were available, while pylint and conda were not installed in this environment.
- `python -m unittest tests.assist_tests.snapshot_cli_test tests.cli_tests.snapshot_test` passed during targeted validation.
- `python -m unittest tests.assist_tests.snapshot_cli_test` passed after the final reporting adjustment.
- `scripts/test` passed.
- `scripts/lint` passed after fixing a test-string line-length issue.
- `scripts/format --check` passed.
- `lrh validate` completed with 0 errors and existing design-proposal lifecycle warnings.
- `lrh snapshot project --project-root . | sed -n '/## Design Proposals/,/## Roadmap/p'` confirmed the new section renders in the repository snapshot.

# Follow-up

No organizer behavior or proposal-file reorganization was added. Existing
repository proposal sets still have validation warnings about unbucketed or
legacy accepted design-proposal metadata; those remain separate content/layout
cleanup work.

# Review Response

Addressed PR review feedback by making snapshot design-proposal loading
best-effort for malformed proposal-tree Markdown files and by changing the
section rendering to valid nested Markdown lists instead of top-level bullets
with four leading spaces. Added regression coverage for malformed notes under
`project/design/proposals/` and refreshed the assist snapshot README note.

# Review Validation

- `scripts/version tools` completed before formatter/lint/test validation;
  Black and Ruff versions were available.
- `python -m unittest tests.assist_tests.snapshot_cli_test` passed.
- `scripts/format --check --diff` passed.
- `scripts/lint` passed.
- `scripts/test` passed.
- `lrh validate` completed with 0 errors and existing design-proposal lifecycle
  warnings.
