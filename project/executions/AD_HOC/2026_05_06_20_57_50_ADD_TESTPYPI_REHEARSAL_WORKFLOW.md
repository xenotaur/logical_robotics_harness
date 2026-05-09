---
execution_id: 2026_05_06_20_57_50_ADD_TESTPYPI_REHEARSAL_WORKFLOW
prompt_id: PROMPT(AD_HOC:ADD_TESTPYPI_REHEARSAL_WORKFLOW)[2026-05-05T23:28:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-05-06T20:57:50+00:00
---

# Summary

Added a focused TestPyPI rehearsal publishing lane and maintainer documentation without enabling production PyPI publishing.

# Result

Created a manual GitHub Actions workflow that requires a `vMAJOR.MINOR.PATCH` tag ref, builds distribution artifacts, runs `scripts/release-smoke "$TAG_UNDER_TEST" --strict-isolation`, uploads the checked artifacts, and publishes to TestPyPI through PyPA Trusted Publishing/OIDC. Updated maintainer release documentation with TestPyPI trusted-publisher setup, manual workflow operation, verification commands, limitations, tag-ref requirements, and the rehearsal-only scope.

# Validation

- `scripts/version tools`
- `scripts/check-workflows`
- `scripts/release-smoke` (failed in this environment while the isolated build attempted package-index access for build requirements and received proxy/tunnel 403 responses)
- `scripts/test`
- `scripts/lint`
- `scripts/format --check --diff`
- `lrh validate`

# Follow-up

Configure the TestPyPI `lrh` trusted publisher for repository `xenotaur/logical_robotics_harness`, workflow `testpypi-rehearsal.yml`, and environment `testpypi` before expecting the rehearsal upload job to succeed. Production PyPI publishing remains intentionally deferred to a future, separate change.
