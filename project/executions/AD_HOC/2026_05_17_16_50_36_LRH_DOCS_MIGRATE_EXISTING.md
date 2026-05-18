---
execution_id: 2026_05_17_16_50_36_LRH_DOCS_MIGRATE_EXISTING
prompt_id: PROMPT(AD_HOC:LRH_DOCS_MIGRATE_EXISTING)[2026-05-17T02:12:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-05-17T16:50:36+00:00
---

# Summary

Migrated the existing LRH release runbook and project setup playbooks into the
`docs/how-to/` hierarchy while preserving short compatibility stubs at the old
paths.

# Result

- Moved the canonical release runbook to `docs/how-to/run-a-release.md`.
- Moved the canonical project setup playbooks to `docs/how-to/project-setup/`.
- Kept compatibility stubs at `docs/release.md`, `docs/project-setup/README.md`,
  and `docs/project-setup/ci.md` for plausible old links.
- Updated documentation navigation, current project references, packaged CI
  request-template path guidance, and template tests to use the new canonical
  paths.
- Left historical execution records, resolved work-item text, and evidence notes
  unchanged when they describe the paths used at the time they were created.

# Validation

- `scripts/version tools` — passed for required Black/Ruff version check; Pylint
  and Conda are not installed in this environment and were reported by the
  version script.
- `lrh prompt check-execution --prompt-id "PROMPT(AD_HOC:LRH_DOCS_MIGRATE_EXISTING)[2026-05-17T02:12:00-04:00]" --project-root .` — passed soft-idempotence gate by reporting no prior execution records before work began.
- `scripts/format --check --diff` — passed during review-feedback follow-up.
- `scripts/lint` — passed.
- `scripts/test` — initially failed because request-template tests still expected
  `docs/project-setup/ci.md`; after updating those expectations, rerun passed
  with 529 tests.
- `rg -n "docs/release\\.md|release\\.md|docs/project-setup|project-setup" README.md docs project` — reviewed stale-link matches; remaining old-path mentions are compatibility stubs or historical project records not updated for this migration.

# Follow-up

- Keep this execution record `in_progress` while the PR is open; update it to
  `landed` with PR and commit metadata after the change lands.
