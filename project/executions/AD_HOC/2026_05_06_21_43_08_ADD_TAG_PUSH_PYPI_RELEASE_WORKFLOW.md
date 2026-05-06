---
execution_id: 2026_05_06_21_43_08_ADD_TAG_PUSH_PYPI_RELEASE_WORKFLOW
prompt_id: PROMPT(AD_HOC:ADD_TAG_PUSH_PYPI_RELEASE_WORKFLOW)[2026-05-05T23:29:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-06T21:43:08+00:00
---

# Summary

Add the production tag-push PyPI release lane for LRH using Trusted Publishing/OIDC, keeping publishing last after release validation, artifact build/check, and installed-wheel smoke validation.

# Result

Added `.github/workflows/release.yml` to run on `v*` tag pushes, validate semantic release tags, install build/check tooling, run `scripts/version verify`, run `scripts/release-smoke --strict-isolation`, upload checked artifacts, and publish to PyPI only from the dependent publishing job with `id-token: write`. Updated maintainer release documentation to cover PyPI Trusted Publisher setup, expected tag format, local pre-tag validation, tag push release commands, post-publish verification, and recovery guidance for failed or partial publishes. Updated script documentation to point production publishing at the Trusted Publishing workflow instead of the disabled local `scripts/publish` path.

# Validation

- `scripts/version tools`
- `scripts/check-workflows`
- `scripts/release-smoke` (failed because the isolated build environment could not fetch build dependency `wheel` from the package index: tunnel connection failed with 403 Forbidden)
- `scripts/test`
- `scripts/lint`
- `scripts/format --check`
- `lrh validate`

# Follow-up

PyPI Trusted Publisher configuration is external to this repository and must be configured for the PyPI `lrh` project before the first production tag-push publish can succeed.
