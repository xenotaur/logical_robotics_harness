---
execution_id: 2026_05_06_06_05_55_ACCEPT_OPTION_D_PYPI_DESIGN
prompt_id: PROMPT(AD_HOC:ACCEPT_OPTION_D_PYPI_DESIGN)[2026-05-05T23:24:00-04:00]
work_item: AD_HOC
status: landed
rerun_of:
pr:
commit:
created_at: 2026-05-06T06:05:55+00:00
---

# Summary

Accepted the tag-push PyPI publishing proposal into LRH canonical
project-control documentation without implementing release automation.

# Result

- Marked `project/design/proposals/tag-push-pypi-publishing/` as
  accepted and updated the proposal index.
- Added canonical design/repository notes that `lrh` is the safe-default
  user-facing distribution and CLI target.
- Recorded `pipx install lrh` as the intended normal CLI install path
  once published.
- Captured Option B implementation sequencing and Option D tag-push PyPI
  publishing through Trusted Publishing.
- Reiterated that the default `lrh` package remains non-agentic, future
  agentic capability remains explicit through `lrh[agentic]` and/or
  `lrh-agentic`, and package boundaries are packaging/governance
  boundaries rather than a security sandbox.

# Validation

- `scripts/version tools` completed; pylint and conda were reported as
  not installed, but the documentation-only validation path proceeded.
- `lrh validate` passed with 0 errors and 0 warnings.
- `git diff --check` passed.

# Follow-up

Implement release readiness in narrow follow-up PRs only: metadata and
package-resource hardening, build/smoke scripts, CI smoke checks,
TestPyPI rehearsal, Trusted Publisher configuration, PyPI tag-push
workflow, docs, then first release.
