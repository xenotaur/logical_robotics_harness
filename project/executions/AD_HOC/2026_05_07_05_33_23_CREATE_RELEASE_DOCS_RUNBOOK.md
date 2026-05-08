---
execution_id: 2026_05_07_05_33_23_CREATE_RELEASE_DOCS_RUNBOOK
prompt_id: PROMPT(AD_HOC:CREATE_RELEASE_DOCS_RUNBOOK)[2026-05-07T12:00:00-04:00]
work_item: AD_HOC
status: landed
rerun_of: N/A
pr: xenotaur/logical_robotics_harness#202
commit: 42ce564
created_at: 2026-05-07T05:33:23+00:00
---

# Summary

Create a documentation-only release runbook and reduce duplicate release procedure material in the main README.

# Result

Added `docs/release.md` as the canonical maintainer release runbook for LRH release validation, tagging, smoke testing, TestPyPI rehearsal, PyPI Trusted Publisher setup, tag-push publishing, post-release verification, failure recovery, and release evidence.

Replaced the long `README.md` release section with a concise pointer to the dedicated runbook.

# Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `scripts/check-workflows`

# Review response

Addressed PR #202 review feedback by finalizing this execution record front matter.
Status is no longer `in_progress`, the PR reference is populated, the original
documentation commit is identified, and `rerun_of` uses an explicit `N/A` sentinel
because this was not a rerun.

# Follow-up

Maintainers still need to perform external TestPyPI/PyPI Trusted Publisher setup, run an actual TestPyPI rehearsal, and capture release evidence when preparing a real release.
