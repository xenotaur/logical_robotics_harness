---
execution_id: 2026_05_06_20_02_40_ADD_CI_INSTALLED_WHEEL_SMOKE
prompt_id: PROMPT(AD_HOC:ADD_CI_INSTALLED_WHEEL_SMOKE)[2026-05-05T23:27:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-06T20:02:40+00:00
---

# Summary

Add focused GitHub Actions coverage that builds LRH artifacts and smoke-tests the installed wheel before any release publishing workflow is introduced.

# Result

Added a pull-request/main-branch/manual workflow that installs development build/check dependencies and runs the existing `scripts/release-smoke --strict-isolation` command. The workflow only has read-only repository permissions and does not configure PyPI credentials, Trusted Publishing, or publishing steps.

# Validation

- `scripts/version tools` passed for the expected Black and Ruff versions.
- `scripts/check-workflows` passed and validated the new workflow YAML.
- `scripts/format --check --diff` passed.
- `scripts/lint` passed.
- `scripts/test` passed.
- `lrh validate` passed.
- `scripts/release-smoke --strict-isolation` was attempted locally, but the isolated build step failed before smoke execution because package-index access returned tunnel `403 Forbidden` while resolving build-system requirements such as `setuptools-scm>=8`.

# Follow-up

Final installed-wheel smoke validation should run in GitHub Actions where the workflow can install build dependencies. Publishing remains intentionally out of scope for this change.
