---
execution_id: 2026_05_06_23_42_48_UPDATE_INSTALL_RELEASE_DOCS_READINESS
prompt_id: PROMPT(AD_HOC:UPDATE_INSTALL_RELEASE_DOCS_READINESS)[2026-05-05T23:30:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-06T23:42:48+00:00
---

# Summary

Update LRH install and release readiness documentation for the first real PyPI publishing path.

# Result

Added user-facing PyPI install guidance that distinguishes `pipx install lrh` as the preferred normal CLI path once published from `pip install lrh` for library, CI, and development environments. Clarified that the default `lrh` distribution is safe-default packaging, not a sandbox guarantee, and that future agentic install forms require a real extra/package first.

Expanded the maintainer release documentation with a first-release readiness checklist covering repository tasks already complete, external/manual PyPI and TestPyPI Trusted Publisher setup, package-name confirmation/reservation, TestPyPI rehearsal expectations, final tag-push release actions, post-publish verification, release-smoke evidence, and failed/partial release handling.

# Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/check-workflows`
- `scripts/test`

# Follow-up

Before the first real PyPI publish, maintainers still need to complete external TestPyPI/PyPI Trusted Publisher setup, confirm or reserve the `lrh` project name on package indexes, run a TestPyPI rehearsal, push the final release tag, and capture release evidence from the workflow/package/install verification artifacts.
