---
execution_id: 2026_05_09_20_05_01_DESIGN_PROPOSAL_PARSER_VALIDATION
prompt_id: PROMPT(AD_HOC:DESIGN_PROPOSAL_PARSER_VALIDATION)[2026-05-09T10:05:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-09T20:05:01+00:00
---

# Summary

Implemented the first parser/model/validation stage for design proposals as
project control-plane artifacts.

# Result

- Added a typed `DesignProposal` runtime model and loader support for
  frontmatter-declared proposal artifacts under `project/design/proposals/`.
- Integrated design-proposal validation with `lrh validate`, including
  lifecycle status, implementation status, traceability fields, duplicate IDs,
  reference checks, `type`/`kind` compatibility, legacy `accepted` handling, and
  lifecycle bucket warnings.
- Added unit coverage for valid metadata, compatibility behavior, schema
  failures, duplicate IDs, warning cases, broken references, and deterministic
  message ordering.
- Documented the machine-readable proposal metadata behavior in the design
  proposals README.

# Validation

- `scripts/version tools` passed before task-phase validation; Black and Ruff
  versions were available and matched the repository workflow expectations.
- `python -m unittest tests.control_tests.design_proposal_test -v` passed.
- `scripts/format --check` initially reported two files needing formatting;
  `scripts/format` was run and the final `scripts/format --check` passed.
- `scripts/lint` initially reported three line-length issues in the new
  validator messages; the messages were wrapped and the final `scripts/lint`
  passed.
- `scripts/test` passed.
- `lrh validate` passed with 0 errors and migration warnings for existing
  unbucketed proposal files plus legacy `accepted` proposal metadata.

# Follow-up

Future PRs may add `lrh design organize`, snapshot reporting, or migration of
existing proposal files into lifecycle buckets. Those items were intentionally
left out of this parser/validation stage.
