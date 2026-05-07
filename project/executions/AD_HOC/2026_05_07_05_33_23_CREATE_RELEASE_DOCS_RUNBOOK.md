---
execution_id: 2026_05_07_05_33_23_CREATE_RELEASE_DOCS_RUNBOOK
prompt_id: PROMPT(AD_HOC:CREATE_RELEASE_DOCS_RUNBOOK)[2026-05-07T12:00:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-07T05:33:23+00:00
---

# Summary

Create a documentation-only release runbook and reduce duplicate release procedure material in the main README.

# Result

Added `docs/release.md` as the canonical maintainer release runbook for LRH release validation, tagging, smoke testing, TestPyPI rehearsal, PyPI Trusted Publisher setup, tag-push publishing, post-release verification, failure recovery, and release evidence.

Replaced the long `README.md` release section with a concise pointer to the dedicated runbook.

# Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/check-workflows`

# Follow-up

Maintainers still need to perform external TestPyPI/PyPI Trusted Publisher setup, run an actual TestPyPI rehearsal, and capture release evidence when preparing a real release.
