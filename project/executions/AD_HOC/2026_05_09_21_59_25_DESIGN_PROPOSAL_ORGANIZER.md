---
execution_id: 2026_05_09_21_59_25_DESIGN_PROPOSAL_ORGANIZER
prompt_id: PROMPT(AD_HOC:DESIGN_PROPOSAL_ORGANIZER)[2026-05-09T10:10:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-05-09T21:59:25+00:00
---

# Summary

Add a design-proposal organizer command for moving recognized proposal Markdown
files into lifecycle buckets derived from authoritative frontmatter `status`.

# Result

Implemented `lrh design organize` and `lrh design organize --apply` with dry-run
planning by default, `accepted` to `adopted/` compatibility, deterministic text
output, skipped invalid/non-proposal files, and collision refusal. Review feedback
was addressed by preserving proposal-set relative paths under lifecycle buckets
and aligning design-proposal index-file ignore behavior across the organizer,
loader, and validator. Updated design proposal and top-level CLI documentation.
Added unit and CLI coverage for the new command behavior.

# Validation

- `scripts/version tools` completed before task-phase validation; Black and Ruff
  were available, while pylint and conda were not installed in this environment.
- `python -m unittest tests.design_tests.organize_test tests.cli_tests.design_test`
  passed.
- `scripts/format --check --diff` passed during review-response validation.
- `scripts/lint` passed.
- `scripts/test` passed.
- `scripts/format --check` passed during initial validation.
- `lrh validate` passed with existing design-proposal lifecycle warnings.
- `lrh design organize` completed as a dry run and reported proposed moves that
  preserve proposal-set relative paths with no collision blocks in the repository's
  current proposal-set layout.

# Follow-up

No immediate follow-up required for the command. Existing repository proposal
sets still contain unbucketed documents, so applying the organizer to this
repository's own project tree remains a separate content/layout migration
decision.
